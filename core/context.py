class RiskContext:
    def __init__(self, ticker):
        self.ticker = ticker

        self.price_series = None
        self.predicted_prices = None

        self.asset_metrics = None
        self.regime = None
        self.forecast_risk = None
        self.stress = None

        self.recommendation = None
        self.explanation = None

        self.adjusted_risk_percent = None