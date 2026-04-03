class RiskContext:
    def __init__(self, ticker):
        self.ticker = ticker

        # Raw data
        self.price_series = None
        self.returns = None
        self.predicted_prices = None

        # Core layers
        self.asset_metrics = None
        self.regime = None
        self.portfolio = None

        # Decision layers
        self.trade = None
        self.stress = None
        self.capital = None
        self.forecast_risk = None

        # Controls
        self.adjusted_risk_percent = None

        # Final outputs
        self.summary_score = None
        self.summary_label = None
        self.recommendation = None
        self.explanation = None