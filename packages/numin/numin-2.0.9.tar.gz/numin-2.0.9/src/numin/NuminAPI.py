import pandas as pd
import requests
from io import StringIO
import os
import base64
import io 
import pickle
from .backtest_wrapper import UserBacktestStrategy
from .utils import Backtest, DataFeed, discretize_features_feed, add_addl_features_feed, add_logical_features_feed
import warnings
import anvil.server
import anvil.media
from anvil import BlobMedia
from pprint import pformat
import codecs 
import torch
from torch.utils.data import Dataset
import numpy as np

warnings.filterwarnings('ignore')

# Class Definition
class NuminDataset(Dataset):
    def __init__(self, samples, targets):
        self.samples = samples
        self.targets = targets

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        # Perform any necessary transformations here
        x = torch.tensor(self.samples[idx]).float()
        y = torch.tensor(self.targets[idx]).long()
        return x, y

class NuminAPI():
    def __init__(self, api_key: str = None):
        """
        Initializes the NuminAPI instance.

        Parameters:
        - api_key (str, optional): The API key for authenticating requests.
        """
        
        print("importing remotely")

        self.api_key = api_key
        self.uplink_key = "U662XILUQK3NTXXRKYGCSDSX-BRX4OESLV4HADBHN" # trader uplink key
        
        anvil.server.connect(self.uplink_key)

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.discretizer_path = os.path.join(current_dir, "utils", "discretizers.pickle")
        
        # with open (self.discretizer_path, 'rb') as f:
        #     self.discretizer = pickle.load(f)
        
        # Published Anvil app's URL
        # https://familiar-subtle-comment.anvil.app
        # self.base_url = "https://beneficial-absolute-depth.anvil.app/_/api" # TEST
        # self.base_url = "https://familiar-subtle-comment.anvil.app/_/api" # Numin BUILD
        self.base_url = "https://numin-tournament.anvil.app/_/api" # Numin PROD

    def get_data(self, data_type: str):
        """
        Fetches the specified type of data (e.g., 'training' or 'round') from the server 
        and returns it as a DataFrame.

        Parameters:
        - data_type (str): The type of data to fetch. Must be 'training' or 'round' or 'validation'.

        Returns:
        - pd.DataFrame: Data from the CSV file.
        """
        if data_type not in ["training", "round", "validation"]:
            return {"error": "Invalid data_type. Must be 'training', 'round' or 'validation'."}

        url = f"{self.base_url}/download_data"
        response = requests.post(url, json={"type": data_type})  # Send type as JSON payload

        if response.status_code == 200:
            if data_type == "round" or data_type == "validation":
                # The endpoint returns the file content; we'll treat response.text as CSV.
                return pd.read_csv(StringIO(response.text))
            elif data_type == "training":
                # Treat the response as a ZIP file and return it as a file-like object
                return io.BytesIO(response.content)
        else:
            return {"error": f"Failed to fetch {data_type} data: {response.text}"}

    def submit_predictions(self, file_path: str):
        """
        Submits predictions to the server by uploading a CSV file.
        Requires API key authentication.
        
        The CSV file must contain the mandatory columns: ["id", "predictions", "round_no"].
        If provided, optional columns ["stop", "target", "tLimit"] must have integer values between 1 and 100.
        
        Parameters:
        - file_path (str): Path to the CSV file.
        
        Returns:
        - dict: JSON response from the server.
        """
        if not self.api_key:
            return {"error": "API key is required to submit predictions."}

        if not os.path.exists(file_path):
            return {"error": f"No such file: '{file_path}'"}

        # Read a few rows to check for required columns
        df = pd.read_csv(file_path, nrows=5)
        required_columns = ["id", "predictions", "round_no"]
        if not all(column in df.columns for column in required_columns):
            return {"error": f"CSV file must contain columns: {required_columns}"}
        
        # If optional columns exist, validate their values
        for col in ['stop', 'target', 'tLimit']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                if ((df[col].dropna() < 1).any() or (df[col].dropna() > 100).any()):
                    return {"error": f"Column '{col}' must have integer values between 1 and 100."}

        url = f"{self.base_url}/upload_predictions"
        with open(file_path, "rb") as f:
            file_content = base64.b64encode(f.read()).decode('utf-8')
            # Create JSON payload
            payload = {
                "api_key": self.api_key,
                "file_name": os.path.basename(file_path),
                "file_content": file_content,
                "content_type": "text/csv"
            }
        
        response = requests.post(url, json=payload)
        try:
            response_data = response.json()  # Parse JSON response
        except ValueError:
            print(f"Raw server response: {response.text}")
            return {"error": f"Server returned non-JSON response: {response.text}"}
        
        if response.status_code == 200:
            if response_data.get("status") == "success":
                return response_data
            else:
                return {"error": f"Failed to submit predictions: {response_data.get('message', 'Unknown error')}"}
        else:
            return {"error": f"Failed to submit predictions: {response.text}"}


    def get_current_round(self):
        """
        Fetches the current round number from the server.

        Returns:
        - str: The current round number.
        """
        
        url = f"{self.base_url}/get_current_round"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return data.get("message")
            else:
                return {"error": f"Failed to get current round: {data.get('message')}"}
        else:
            return {"error": f"Failed to get current round: {response.text}"}
    
    def fetch_validation_data(self, date):
        """
        Fetches validation data for a given date from the Anvil API.

        Parameters:
        - date (str): Date in 'YYYY-MM-DD' format.

        Returns:
        - pd.DataFrame: Validation data if successful.
        - dict: Error message if unsuccessful.
        """
        url = f"{self.base_url}/download_validation_data"
        payload = {"date": date}
        
        try:
            response = requests.post(url, json=payload)

            if response.status_code == 200:
                # If server returns a JSON error message, handle it
                if "application/json" in response.headers.get("Content-Type", ""):
                    return response.json()
                
                # Otherwise, assume it's a CSV file
                return pd.read_csv(io.StringIO(response.text))

            return {"status": "error", "message": f"Failed to fetch validation data: {response.text}"}

        except requests.RequestException as e:
            return {"status": "error", "message": f"Request failed: {str(e)}"} 
    
    def get_validation_dates(self):
        """
        Fetches the list of dates for which a validation CSV file is available from the server.

        Returns:
        - list: List of date strings in 'YYYY-MM-DD' format if successful.
        - dict: An error message dictionary if an error occurs.
        """
        url = f"{self.base_url}/get_validation_dates"
        try:
            response = requests.get(url, timeout=10)
        except requests.RequestException as req_err:
            return {"error": f"Request failed: {str(req_err)}"}

        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                return {"error": f"Non-JSON response received: {response.text}"}
            
            if data.get("status") == "success":
                dates = data.get("dates")
                if dates is None:
                    return {"error": "No dates key in response."}
                return dates
            else:
                return {"error": f"Server error: {data.get('message', 'Unknown error')}"}
        else:
            return {"error": f"Failed to fetch validation dates. HTTP Status {response.status_code}: {response.text}"}

    
    def run_backtest(self, user_strategy, date=None, val_data=None, val_df=None,result_type="results"):
        print("Numin v1 also runs on local data specify val_data a csv file")
        """
        Runs backtesting on a given user strategy.

        Parameters:
        - user_strategy (function, required): A function that takes a pandas DataFrame and returns predictions.
        - date (str, required): Date in 'YYYY-MM-DD' format (mandatory).
        - val_data (str, optional): Path to a CSV file containing validation data. If provided, `date` must also be given.
        - result_type (str): "results" to return bt.results, "returns" to return bt.returns.

        Returns:
        - dict: Backtest results or returns based on `result_type`.
        """

        # Validation: `date` is mandatory
        if not date:
            raise ValueError("You must provide a 'date' (YYYY-MM-DD).")

        # Validation: If `val_data` is given, `date` must also be given (which is already ensured above)
        if val_data and not os.path.exists(val_data):
            raise FileNotFoundError(f"File not found: {val_data}")

        # Load validation data
        if val_data:  # Load from CSV
            print(f"Loading data from provided CSV: {val_data}")
            df = pd.read_csv(val_data)
        if val_df is not None:
            df = val_df
        else:  # Fetch from Anvil API
            print(f"Fetching validation data for date: {date}")
            df = self.fetch_validation_data(date)

            # If API returns an error (dict instead of DataFrame), stop execution
            if isinstance(df, dict) and df.get("status") == "error":
                return df

        # Convert tradeframe (ensure proper column formatting)
        self._convert_tradeframe(df, date=date)

        # Create DataFeed object
        tickers_list = list(df["id"].unique())
        dataFeed = DataFeed(tickers=tickers_list[:50], dfgiven=True, df=df)

        # Add additional features
        add_addl_features_feed(feed=dataFeed, tickers=dataFeed.tickers, drop_ta=False)
        # _ = add_logical_features_feed(dataFeed)

        # Load discretizers
        # with open(self.discretizer_path, "rb") as f:
        #     discretizers = pickle.load(f)
        # DkD = discretizers[2]

        # # Discretize features
        # discretize_features_feed(dataFeed, DkD, "alllog")

        # Initialize Backtest object
        bt = Backtest(
            dataFeed,
            tickers=dataFeed.tickers,
            add_features=False,
            target=0.05,
            stop=0.01,
            txcost=0.001,
            loc_exit=False,
            scan=True,
            topk=10,
            deploy=True,
            save_dfs=False,
            t_limit=10
        )

        # Initialize user strategy wrapper
        user_strategy_wrapper = UserBacktestStrategy(user_strategy)

        # Run backtest
        bt.run_all(tickers=dataFeed.tickers, model=user_strategy_wrapper)

        # Return requested result
        if result_type == "results":
            return bt.results
        elif result_type == "returns":
            return bt.returns
        else:
            raise ValueError("Invalid result_type. Must be 'results' or 'returns'.")

    
    def _convert_tradeframe(self, df, date):
        """
        Converts the raw validation DataFrame into the proper tradeframe format.
        """
        df["Open"] = df["Open_n"]
        df["High"] = df["High_n"]
        df["Low"] = df["Low_n"]
        df["Close"] = df["Close_n"]
        df["ticker"] = df["id"]
        df["Volume"] = 1
        basedt = pd.to_datetime(f"{date} 09:15:00")

        def setdt(row):
            if row["row_num"] < 75:
                return basedt - pd.Timedelta(days=1) + pd.Timedelta(minutes=5 * row["row_num"])
            else:
                return basedt + pd.Timedelta(minutes=5 * (row["row_num"] - 75))

        def getdt(row):
            return row["Datetime"].strftime("%d-%b-%Y")

        df["Datetime"] = df.apply(setdt, axis=1)
        df["Date"] = df.apply(getdt, axis=1)
      
    def upload_file(self, file, user_id=None, filename=None):
        print("Numin v1 upload is out of service")
        return
        try:
            # Get filename
            final_filename = user_id + "_" + (filename if filename else file.filename)
            print(final_filename)
            # Connect to Anvil server
            anvil.server.connect("FMQBTGZ2T6DRDZISLDZ3XMIH-BRX4OESLV4HADBHN-CLIENT")
            # anvil.server.connect(os.getenv("ANVIL_CLIENT_KEY"))
            print("Connected to Anvil server")
            # Convert uploaded file directly to anvil media
            file_content = file.read()
            anvil_file = BlobMedia("application/python", file_content, name=final_filename)
            success = anvil.server.call('upload_files_remote', anvil_file)
            print("File uploaded successfully")
            if not success:
                error_msg = "Failed to upload file to remote storage"
                return {"error": error_msg}

            success_msg = f"File uploaded successfully as {final_filename}"
            return {"message": success_msg}
            
        except Exception as e:
            error_msg = f"Upload error: {str(e)}"
            return {"error": error_msg}

    def deploy_file(self, filename: str, user_id: str):
        print("Numin v1 is deploy is out of service")
        return
        # return "Deployment temporarily not available"
        try:
            # anvil.server.connect(os.getenv("ANVIL_CLIENT_KEY"))
            anvil.server.connect("FMQBTGZ2T6DRDZISLDZ3XMIH-BRX4OESLV4HADBHN-CLIENT")
            print("Server Connected!")
            success = anvil.server.call('deploy_file_remote', filename, user_id)
            print("File deployed successfully")
            if not success:
                error_msg = "Failed to deploy file"
                return {"error": error_msg}
            
            success_msg = f"File deployed successfully for user: {user_id}"
            return {"message": success_msg}
        except Exception as e:
            error_msg = f"Deployment error: {str(e)}"
            return {"error": error_msg}
        
    def check_file_running(self, filename: str, user_id: str):
        print("Numin v1 is out of service")
        return
        # return "Deployment temporarily not available"
        """
        Checks if a file is currently running for a given user.

        Parameters:
            filename (str): The name of the file to check.
            user_id (str): The ID of the user.

        Returns:
            dict: A dictionary containing the status and message.
        """
        try:
            anvil.server.connect("FMQBTGZ2T6DRDZISLDZ3XMIH-BRX4OESLV4HADBHN-CLIENT")
            result = anvil.server.call('check_file_running', filename, user_id)
            return result
        except Exception as e:
            return {"error": f"Error checking file status: {str(e)}"}

    def kill_file_process(self, filename: str, user_id: str):
        print("Numin v1 kill is out of service")
        return
        """
        Kills a running process for a given user.

        Parameters:
            filename (str): The name of the file to kill.
            user_id (str): The ID of the user.

        Returns:
            dict: A dictionary containing the status and message.
        """
        try:
            anvil.server.connect("FMQBTGZ2T6DRDZISLDZ3XMIH-BRX4OESLV4HADBHN-CLIENT")
            result = anvil.server.call('kill_file_process', filename, user_id)
            return result
        except Exception as e:
            return {"error": f"Error killing process: {str(e)}"}

    def get_ord_ex_pos(self, strategies, mode="live"):
        """
        Fetches order, exit, and position data from the Anvil server for the specified strategies
        and computes a cumulative return based on the positions' pnl.
        
        Parameters:
            strategies (list): A list of strategy names to query.
            mode (str): Either "live" or "sim" to choose the correct server endpoint.
        
        Returns:
            dict: A dictionary with keys:
                - "orders"
                - "exits"
                - "positions"
                - "tick_data"
                - "placed_exits"
                - "tickers"
                - "strat_tickers"
                - "cumulative_return"
            or None in case of error.
        """
        try:
            if mode.lower() == "live":
                result = anvil.server.call("getOrdExPos_live", strategies)
            else:
                result = anvil.server.call("getOrdExPos_simulation", strategies)
            
            # Expected tuple from the server:
            # (orders, exits, positions, tick_data, placed_exits, tickers, strat_tickers)
            orders, exits, positions, tick_data, placed_exits, tickers, strat_tickers = result
            
            # Compute cumulative return if positions is a DataFrame and contains a 'pnl' column.
            cumulative_return = 0
            try:
                if isinstance(positions, pd.DataFrame) and 'pnl' in positions.columns:
                    cumulative_return = positions['pnl'].sum()
            except Exception as e:
                print("Warning: Unable to compute cumulative return:", e)
            
            return {
                "orders": orders,
                "exits": exits,
                "positions": positions,
                "tick_data": tick_data,
                "placed_exits": placed_exits,
                "tickers": tickers,
                "strat_tickers": strat_tickers,
                "cumulative_return": cumulative_return
            }
        except Exception as e:
            # print("Error in get_ord_ex_pos:", e)
            print("Error: Please check if you are calling the correct mode (live/sim)")
            return None

    @staticmethod
    def format_returns_summary(data, user_strategy=None):
        """
        Transforms the raw dictionary returned from get_ord_ex_pos into a clean,
        human-readable summary. In addition, all ticker names are encoded using ROT13.
        
        Parameters:
          data (dict): Dictionary with keys including:
              - orders
              - exits
              - positions (list of dicts)
              - tick_data (dict mapping ticker -> list of tick dicts)
              - placed_exits
              - tickers (list)
              - strat_tickers (dict)
              - cumulative_return
          user_strategy (str): If provided, only shows tickers (and associated info)
                               for that strategy.
                                
        Returns:
          str: A formatted multi-line string summarizing the key information.
        """
        lines = []
        lines.append("==== Returns Summary ====")
        
        # Orders and Exits
        lines.append("Orders: {}".format(data.get("orders", [])))
        lines.append("Exits: {}".format(data.get("exits", [])))
        
        # Positions
        lines.append("Positions:")
        positions = data.get("positions", [])
        if positions:
            try:
                pos_df = pd.DataFrame(positions)
                cols = ["ticker", "pnl", "stop", "target", "tLimit", "status", "datetime"]
                cols = [c for c in cols if c in pos_df.columns]
                # Apply ROT13 encoding to the ticker column if present.
                if "ticker" in cols:
                    pos_df["ticker"] = pos_df["ticker"].apply(lambda t: codecs.encode(t, 'rot13'))
                lines.append(pos_df[cols].to_string(index=False))
            except Exception as e:
                lines.append("  Error formatting positions: {}".format(e))
        else:
            lines.append("  No positions.")
        
        # Tick Data: Summarize by showing the latest tick for each ticker (encoded via ROT13)
        lines.append("Tick Data:")
        tick_data = data.get("tick_data", {})
        if tick_data:
            for ticker, ticks in tick_data.items():
                if ticks:
                    latest = ticks[-1]
                    dt = latest.get("datetime", "N/A")
                    close = latest.get("Close", "N/A")
                    encoded_ticker = codecs.encode(ticker, 'rot13')
                    lines.append("  {}: datetime: {}, Close: {}".format(encoded_ticker, dt, close))
                else:
                    encoded_ticker = codecs.encode(ticker, 'rot13')
                    lines.append("  {}: No data".format(encoded_ticker))
        else:
            lines.append("  No tick data.")
        
        lines.append("Placed Exits: {}".format(data.get("placed_exits", {})))
        
        # Tickers: Show ROT13-encoded tickers.
        raw_tickers = data.get("tickers", [])
        encoded_tickers = [codecs.encode(t, 'rot13') for t in raw_tickers]
        lines.append("Tickers: {}".format(encoded_tickers))
        
        # Strategy Tickers: If user_strategy is provided, filter only that one.
        strat_tickers = data.get("strat_tickers", {})
        if user_strategy in strat_tickers:
            encoded_st_tickers = [codecs.encode(t, 'rot13') for t in strat_tickers[user_strategy]]
            lines.append("Strategy Tickers: {}".format(encoded_st_tickers))
        else:
            # show that the current strategy is not yet submitted predictions
            lines.append("Strategy Tickers: No predictions submitted for this strategy.")
        
        lines.append("Cumulative Return: {}".format(data.get("cumulative_return", 0)))
        return "\n".join(lines)

    def show_returns(self, user_id, mode="live"):
        """
        Retrieves order/exit/position data from the Anvil server for the given user_id,
        constructs the strategy name as "NUMIN_user_<user_id>", and displays a formatted
        summary (with ROT13 encoding of all ticker names) including the cumulative return.

        Parameters:
            user_id (str): The user ID; the strategy is assumed to be named "NUMIN_user_<user_id>".
            mode (str): Either "live" or "sim" (simulation); default is "live".
            
        Returns:
            str: A formatted summary string.
        """
        # Ensure connection to the Anvil uplink server.
        try:    
            anvil.server.connect(self.uplink_key)
        except Exception as e: 
            print("Error connecting to Anvil server:", e)
            return None
        
        # Build the strategy name from user_id.
        user_strategy = f"NUMIN_user_{user_id}"
        strategies = [user_strategy]
        
        # Fetch data from the server.
        try:
            data = self.get_ord_ex_pos(strategies, mode=mode)
        except Exception as e:
            print("Error fetching order/exit/position data:", e)
            return None
        
        if data is None:
            print("Error: No data returned from the server.")
            return None
        
        # Format the retrieved data into a human-readable summary,
        # applying ROT13 encoding to all ticker names.
        summary = NuminAPI.format_returns_summary(data, user_strategy=user_strategy)
        # print(summary)
        return summary

    def display_results(self,backtest_results, validation_dataframe, indicators):
            """
            Displays backtest results in a readable format
            Inputs:
            backtest_results - output of run_backtest
            valdiation_datafrale - validation data downloaded from server as a dataframe
            indicators - list of additional indictors to be displayed, e.g. used for entry
            Returns: List of records with Entry, Exit prices, row numbers, buy/sell, and indicators requested
            """
            response=backtest_results
            df=validation_dataframe
            resultL=[]
            for id in response:
                tf=df.loc[df['id']==id]
                lr=tf.iloc[-1]['row_num']
                for date in response[id]:
                    rewL=response[id][date]['rew']
                    actL=response[id][date]['acts']
                    for r,a in zip(rewL,actL):
                        row={}
                        row['id'],row['Date'],row['P/L'],row['B/S']=id,date,r[1],a[0]
                        er=r[0]+75
                        xr=75+r[2]
                        if xr==148: xr=lr
                        elif xr==er: xr=er
                        else: xr=xr-1
                        row['Entry']=tf.loc[tf['row_num']==er]['Close_n'].values[0]
                        row['Exit']=tf.loc[tf['row_num']==xr]['Close_n'].values[0]
                        row['verP/L']=100*(row['B/S']*(row['Exit']-row['Entry'])-.001*abs(row['Entry']))/row['Entry']
                        row['Entry Row'],row['Exit Row']=er,xr
                        row['row_num']=tf.loc[tf['row_num']==er]['row_num'].values[0]
                        for ind in indicators:
                            row[ind]=tf.loc[tf['row_num']==er][ind].values[0]
                        resultL.append(row)
            return resultL
    
    def get_data_for_month(self,year,month,batch_size=4,window_size=100,target_type='rank'):
        """
        Returns a torch dataset for the given year and month of Nifty 50 returns
        Dimension of each day is 100,50. Returns tensor of shape [batch_size,window_size,50 for features.
        Targets are next day returns / ranked returns of shape [batch_size,50]
        """
        XR,YR=anvil.server.call('get_data_for_month',year=2025,month=month,batch_size=batch_size,window_size=window_size,target_type=target_type)
        numin_dataset = NuminDataset(XR, YR)
        return numin_dataset 
    
    def compute_pnl(self,positions,targets):
        if hasattr(positions, 'detach'): positions = positions.detach().cpu().numpy()
        if hasattr(targets, 'detach'): targets = targets.detach().cpu().numpy()
        positions = np.asarray(positions)
        targets = np.asarray(targets)
        if positions.shape[-1] != targets.shape[-1]:
            raise ValueError("Positions and targets must have the same number of columns")
        if positions.shape[-1] != 50:
            raise ValueError("Positions and targets must have dimensions of n,50")
        return anvil.server.call('gen_pnl',positions,targets)

