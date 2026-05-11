import time
import torch
import numpy as np
import pandas as pd
import warnings
import yfinance as yf
import traceback
import ta
from sklearn.preprocessing import RobustScaler
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet, GroupNormalizer, NaNLabelEncoder

# Suppress annoying PyTorch Lightning and Pandas warnings in the terminal
warnings.filterwarnings("ignore")

class TFTService:
    def __init__(self, model_path="tft_Fold 3-v1.ckpt"):
        print(f"\n[🧠 SYSTEM] Booting up PyTorch Temporal Fusion Transformer...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[🧠 SYSTEM] Hardware acceleration: {self.device}")
        
        try:
            self.model = TemporalFusionTransformer.load_from_checkpoint(model_path)
            self.model.to(self.device)
            self.model.eval()
            print(f"[✅ SYSTEM] Champion TFT Model loaded successfully.")
            self.is_loaded = True
        except Exception as e:
            print(f"[❌ SYSTEM] Warning: Could not load TFT model at {model_path}. Error: {e}")
            self.is_loaded = False

    def predict_direction(self, ticker: str) -> dict:
        start_time = time.time()
        
        if not self.is_loaded:
            return {"error": "PyTorch model is offline. Cannot make predictions."}

        try:
            ticker = ticker.upper()
            
            # 1. Fetch enough historical data to satisfy lookback windows (150 days is safe)
            df = yf.download(ticker, period="150d", progress=False)
            spy = yf.download("SPY", period="150d", progress=False)
            
            if df.empty or spy.empty:
                return {"error": f"Could not fetch market data for {ticker} or SPY."}
                
            # Flatten multi-index if necessary (newer yfinance versions)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            if isinstance(spy.columns, pd.MultiIndex):
                spy.columns = spy.columns.droplevel(1)

            # 2. Recreate SPY Macro Features
            spy = spy[['Close']].copy()
            spy['spy_return'] = np.log(spy['Close'] / spy['Close'].shift(1))
            spy['spy_volatility_20d'] = spy['spy_return'].rolling(20).std()
            spy_features = spy[['spy_return', 'spy_volatility_20d']].dropna()
            
            # 3. Merge and Recreate Asset Features
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            df = pd.merge(df, spy_features, left_index=True, right_index=True, how='inner')
            
            df['target_return'] = np.log(df['Close'] / df['Close'].shift(1))
            df['asset_to_spy_correlation'] = df['target_return'].rolling(window=20).corr(df['spy_return'])
            
            # Target clipping
            q01 = df['target_return'].quantile(0.01)
            q99 = df['target_return'].quantile(0.99)
            df['target_clipped'] = df['target_return'].clip(q01, q99)
            
            # 🟢 THE FIX: Save a clean, unscaled copy of the dollar price BEFORE we scale everything
            df['Raw_Close'] = df['Close'].copy() 
            
            # Base Technicals
            df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
            macd_inst = ta.trend.MACD(df['Close'], window_fast=12, window_slow=26, window_sign=9)
            df['MACD'] = macd_inst.macd()
            df['MACD_Signal'] = macd_inst.macd_signal()
            df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close'], window=14).average_true_range()
            
            # Momentum & Volatility
            df['returns'] = df['Close'].pct_change()
            df['volatility_20d'] = df['returns'].rolling(20).std()
            df['momentum_5d'] = df['Close'].pct_change(5)
            df['ma_7d'] = df['Close'].rolling(7).mean()
            df['ma_21d'] = df['Close'].rolling(21).mean()
            df['ma_crossover'] = (df['ma_7d'] - df['ma_21d']) / df['Close']
            
            for lag in [1, 2, 3, 5, 10, 20]:
                df[f'return_lag_{lag}'] = df['target_return'].shift(lag)
            for period in [5, 10, 20]:
                df[f'roc_{period}'] = df['Close'].pct_change(periods=period)
                
            high_14 = df['High'].rolling(14).max()
            low_14 = df['Low'].rolling(14).min()
            df['stoch_k'] = (df['Close'] - low_14) / (high_14 - low_14 + 1e-8) * 100
            df['williams_r'] = (high_14 - df['Close']) / (high_14 - low_14 + 1e-8) * -100
            
            rolling_mean = df['Close'].rolling(20).mean()
            rolling_std = df['Close'].rolling(20).std()
            df['bb_position'] = (df['Close'] - (rolling_mean - 2 * rolling_std)) / (4 * rolling_std + 1e-8)
            df['hist_vol_20'] = df['target_return'].rolling(20).std() * np.sqrt(252)
            df['volume_ratio'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-8)
            df['obv'] = (np.sign(df['Close'].diff()) * df['Volume']).cumsum()
            
            df.dropna(inplace=True)
            
            # 4. Time encoding & Categoricals
            df.reset_index(inplace=True)
            df['day_sin'] = np.sin(2 * np.pi * df['Date'].dt.dayofweek / 5)
            df['day_cos'] = np.cos(2 * np.pi * df['Date'].dt.dayofweek / 5)
            df['month_sin'] = np.sin(2 * np.pi * df['Date'].dt.month / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['Date'].dt.month / 12)
            
            df['asset'] = ticker
            df['month'] = df['Date'].dt.month.astype(str).astype("category")
            df['day_of_week'] = df['Date'].dt.dayofweek.astype(str).astype("category")
            
            # 5. Scaling (Exactly as done in training)
            KNOWN_REALS = ["time_idx", "day_sin", "day_cos", "month_sin", "month_cos"]
            UNKNOWN_REALS = [
                "Close", "High", "Low", "Open", "Volume",
                "RSI", "MACD", "MACD_Signal", "ATR",
                "volatility_20d", "momentum_5d", "ma_7d", "ma_21d", "ma_crossover",
                "return_lag_1", "return_lag_2", "return_lag_3", "return_lag_5", "return_lag_10", "return_lag_20",
                "roc_5", "roc_10", "roc_20", "stoch_k", "williams_r",
                "bb_position", "hist_vol_20", "volume_ratio", "obv",
                "spy_return", "spy_volatility_20d", "asset_to_spy_correlation"
            ]
            
            df[UNKNOWN_REALS] = df[UNKNOWN_REALS].astype(float)
            scaler = RobustScaler()
            df[UNKNOWN_REALS] = scaler.fit_transform(df[UNKNOWN_REALS])
            
            # Keep only the exact sequence length needed (max_encoder_length + max_prediction_length)
            req_len = self.model.hparams.max_encoder_length + 1 
            df = df.tail(req_len).reset_index(drop=True)
            df['time_idx'] = np.arange(len(df))

            # 6. Build the PyTorch Dataset for Inference
            dataset = TimeSeriesDataSet(
                df, time_idx="time_idx", target="target_clipped", group_ids=["asset"],
                max_encoder_length=self.model.hparams.max_encoder_length, 
                max_prediction_length=1,
                static_categoricals=["asset"], 
                time_varying_known_categoricals=["month", "day_of_week"],
                time_varying_known_reals=KNOWN_REALS,
                time_varying_unknown_reals=UNKNOWN_REALS,
                target_normalizer=GroupNormalizer(groups=["asset"], method="standard", transformation=None, center=True),
                categorical_encoders={"month": NaNLabelEncoder(add_nan=True), "day_of_week": NaNLabelEncoder(add_nan=True)},
                add_relative_time_idx=True, add_target_scales=True, add_encoder_length=True,
                predict_mode=True # Tells dataset this is for active inference
            )
            
            dataloader = dataset.to_dataloader(train=False, batch_size=1, num_workers=0)
            
            # 7. Make the Prediction
            # 7. Make the Prediction
            with torch.no_grad():
                raw_output = self.model.predict(
                    dataloader, 
                    mode="quantiles", 
                    return_x=False, 
                    trainer_kwargs={"accelerator": "auto", "enable_progress_bar": False, "enable_model_summary": False}
                )
                
            predicted_return = raw_output[0][0][1].cpu().item()
            last_close = float(df['Raw_Close'].iloc[-1]) 
            
            # 🟢 ADD THESE THREE PRINT STATEMENTS:
            print("\n" + "!"*50)
            print(f"TRACER: I am using the NEW math! last_close={last_close}")
            print("!"*50 + "\n")
            
            predicted_price = last_close * np.exp(predicted_return) 
            predicted_direction = "UP" if predicted_return > 0 else "DOWN"
            
            execution_time = round((time.time() - start_time) * 1000, 2)
            
            return {
                "ticker": ticker,
                "predicted_direction": predicted_direction,
                "predicted_price": round(predicted_price, 2),
                "last_close_price": round(last_close, 2),
                "inference_time_ms": execution_time,
                "model_architecture": "PyTorch Temporal Fusion Transformer (TFT) - Macro Enabled"
            }
            
        except Exception as e:
            print(f"\n[🐞 DEBUG ERROR] PyTorch Pipeline Crashed!")
            traceback.print_exc()
            return {"error": f"Failed to calculate prediction features: {str(e)}"}