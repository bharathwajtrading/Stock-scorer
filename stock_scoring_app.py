# Comprehensive Scoring Implementation for Value, Momentum, Safety, and Quality Metrics

import pandas as pd
import numpy as np

class StockScoring:
    def __init__(self, stock_data):
        self.stock_data = stock_data

    def score_value(self):
        # Scoring based on P/E and P/B ratios
        pe_score = np.where(self.stock_data['PE'] < 15, 5, np.where(self.stock_data['PE'] < 20, 3, 1))
        pb_score = np.where(self.stock_data['PB'] < 1, 5, np.where(self.stock_data['PB'] < 3, 3, 1))
        return pe_score + pb_score

    def score_momentum(self):
        # Scoring based on 200DMA and RSI
        rsi_score = np.where(self.stock_data['RSI'] < 30, 5, np.where(self.stock_data['RSI'] < 70, 3, 1))
        return rsi_score

    def score_safety(self):
        # Scoring based on Debt/Equity and Beta
        debt_eq_score = np.where(self.stock_data['DebtEq'] < 1, 5, np.where(self.stock_data['DebtEq'] < 2, 3, 1))
        beta_score = np.where(self.stock_data['Beta'] < 1, 5, 3)
        return debt_eq_score + beta_score

    def score_quality(self):
        # Scoring based on Op Margin, FCF, EPS, Div Yield, ROE
        om_score = np.where(self.stock_data['OpMargin'] > 20, 5, np.where(self.stock_data['OpMargin'] > 10, 3, 1))
        fcf_score = np.where(self.stock_data['FCF'] > 0, 5, 1)
        eps_score = np.where(self.stock_data['EPS'] > 2, 5, 1)
        div_yield_score = np.where(self.stock_data['DivYield'] > 3, 5, 1)
        roe_score = np.where(self.stock_data['ROE'] > 15, 5, 3)
        return om_score + fcf_score + eps_score + div_yield_score + roe_score

    def calculate_scores(self):
        self.stock_data['ValueScore'] = self.score_value()
        self.stock_data['MomentumScore'] = self.score_momentum()
        self.stock_data['SafetyScore'] = self.score_safety()
        self.stock_data['QualityScore'] = self.score_quality()
        return self.stock_data

# Example usage:
# stock_data = pd.DataFrame({...})  # Load your stock data here
# stock_scorer = StockScoring(stock_data)
# scores = stock_scorer.calculate_scores()

