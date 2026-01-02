"""Tests for QGARP analysis computation."""

import pytest

from gurufocus_api.models.financials import FinancialPeriod, FinancialStatements
from gurufocus_api.models.keyratios import (
    GrowthRatios,
    KeyRatios,
    LiquidityRatios,
    PerShareData,
    ProfitabilityRatios,
    SolvencyRatios,
    ValuationRatios,
)
from gurufocus_api.models.summary import (
    GeneralInfo,
    PriceInfo,
    StockSummary,
    ValuationMetrics,
)
from gurufocus_api.models.summary import (
    QualityScores as SummaryQualityScores,
)
from gurufocus_mcp.analysis.qgarp import (
    _calculate_bv_growth,
    _calculate_rule1,
    _check_threshold,
    compute_qgarp_analysis,
)
from gurufocus_mcp.models.qgarp import (
    BigFourGrowth,
    FinancialStrength,
    GateDecision,
    GrowthMetric,
    QGARPScreen,
    QualityScores,
    ScreenCriterion,
    ScreenResult,
    SummaryScore,
    ValuationAnalysis,
)


class TestScreenResult:
    """Tests for screening criteria pass/fail logic."""

    def test_check_threshold_greater_than_pass(self) -> None:
        """Test > threshold passes when value exceeds threshold."""
        result = _check_threshold(15.0, ">", 10.0)
        assert result == ScreenResult.PASS

    def test_check_threshold_greater_than_fail(self) -> None:
        """Test > threshold fails when value below threshold."""
        result = _check_threshold(5.0, ">", 10.0)
        assert result == ScreenResult.FAIL

    def test_check_threshold_less_than_pass(self) -> None:
        """Test < threshold passes when value below threshold."""
        result = _check_threshold(0.3, "<", 0.5)
        assert result == ScreenResult.PASS

    def test_check_threshold_less_than_fail(self) -> None:
        """Test < threshold fails when value exceeds threshold."""
        result = _check_threshold(0.8, "<", 0.5)
        assert result == ScreenResult.FAIL

    def test_check_threshold_none_returns_na(self) -> None:
        """Test None value returns N/A."""
        result = _check_threshold(None, ">", 10.0)
        assert result == ScreenResult.NA


class TestQGARPScreen:
    """Tests for QGARP screening criteria."""

    def test_screen_pass_count_all_pass(self) -> None:
        """Test pass count when all criteria pass."""
        screen = QGARPScreen(
            roic=ScreenCriterion(name="ROIC", threshold=">10%", result=ScreenResult.PASS),
            revenue_growth_5y=ScreenCriterion(
                name="Revenue Growth", threshold=">10%", result=ScreenResult.PASS
            ),
            eps_growth_5y=ScreenCriterion(
                name="EPS Growth", threshold=">10%", result=ScreenResult.PASS
            ),
            debt_to_equity=ScreenCriterion(name="D/E", threshold="<0.5", result=ScreenResult.PASS),
            pe_ratio=ScreenCriterion(name="P/E", threshold="<40", result=ScreenResult.PASS),
        )
        assert screen.pass_count == 5
        assert screen.screen_passed is True

    def test_screen_pass_count_some_fail(self) -> None:
        """Test pass count with some failures."""
        screen = QGARPScreen(
            roic=ScreenCriterion(name="ROIC", threshold=">10%", result=ScreenResult.PASS),
            revenue_growth_5y=ScreenCriterion(
                name="Revenue Growth", threshold=">10%", result=ScreenResult.FAIL
            ),
            eps_growth_5y=ScreenCriterion(
                name="EPS Growth", threshold=">10%", result=ScreenResult.PASS
            ),
            debt_to_equity=ScreenCriterion(name="D/E", threshold="<0.5", result=ScreenResult.PASS),
            pe_ratio=ScreenCriterion(name="P/E", threshold="<40", result=ScreenResult.FAIL),
        )
        assert screen.pass_count == 3
        assert screen.screen_passed is False

    def test_screen_passed_threshold_at_4(self) -> None:
        """Test screen passes with exactly 4/5."""
        screen = QGARPScreen(
            roic=ScreenCriterion(name="ROIC", threshold=">10%", result=ScreenResult.PASS),
            revenue_growth_5y=ScreenCriterion(
                name="Revenue Growth", threshold=">10%", result=ScreenResult.PASS
            ),
            eps_growth_5y=ScreenCriterion(
                name="EPS Growth", threshold=">10%", result=ScreenResult.PASS
            ),
            debt_to_equity=ScreenCriterion(name="D/E", threshold="<0.5", result=ScreenResult.PASS),
            pe_ratio=ScreenCriterion(name="P/E", threshold="<40", result=ScreenResult.FAIL),
        )
        assert screen.pass_count == 4
        assert screen.screen_passed is True


class TestQualityScores:
    """Tests for quality score assessments."""

    def test_altman_status_safe(self) -> None:
        """Test Altman Z-Score safe zone."""
        scores = QualityScores(altman_z_score=3.5)
        assert scores.altman_status == "Safe"

    def test_altman_status_grey_zone(self) -> None:
        """Test Altman Z-Score grey zone."""
        scores = QualityScores(altman_z_score=2.5)
        assert scores.altman_status == "Grey Zone"

    def test_altman_status_distress(self) -> None:
        """Test Altman Z-Score distress zone."""
        scores = QualityScores(altman_z_score=1.5)
        assert scores.altman_status == "Distress"

    def test_altman_status_none(self) -> None:
        """Test Altman Z-Score when None."""
        scores = QualityScores(altman_z_score=None)
        assert scores.altman_status == "N/A"

    def test_quality_assessment_strong(self) -> None:
        """Test quality assessment for high GF score."""
        scores = QualityScores(gf_score=85)
        assert scores.quality_assessment == "Strong"

    def test_quality_assessment_moderate(self) -> None:
        """Test quality assessment for moderate GF score."""
        scores = QualityScores(gf_score=65)
        assert scores.quality_assessment == "Moderate"

    def test_quality_assessment_weak(self) -> None:
        """Test quality assessment for low GF score."""
        scores = QualityScores(gf_score=45)
        assert scores.quality_assessment == "Weak"


class TestFinancialStrength:
    """Tests for financial strength verdicts."""

    def test_verdict_pass(self) -> None:
        """Test PASS verdict with healthy metrics."""
        strength = FinancialStrength(
            debt_to_equity=0.3,
            high_debt_flag=False,
            low_coverage_flag=False,
        )
        assert strength.verdict == "PASS"

    def test_verdict_pass_with_caution(self) -> None:
        """Test PASS WITH CAUTION for elevated D/E."""
        strength = FinancialStrength(
            debt_to_equity=0.6,
            high_debt_flag=False,
            low_coverage_flag=False,
        )
        assert strength.verdict == "PASS WITH CAUTION"

    def test_verdict_fail_high_debt(self) -> None:
        """Test FAIL verdict for high debt."""
        strength = FinancialStrength(
            debt_to_equity=1.0,
            high_debt_flag=True,
            low_coverage_flag=False,
        )
        assert strength.verdict == "FAIL"

    def test_verdict_fail_low_coverage(self) -> None:
        """Test FAIL verdict for low interest coverage."""
        strength = FinancialStrength(
            debt_to_equity=0.3,
            high_debt_flag=False,
            low_coverage_flag=True,
        )
        assert strength.verdict == "FAIL"


class TestGrowthMetric:
    """Tests for growth metric consistency."""

    def test_consistent_above_10_all_pass(self) -> None:
        """Test consistency when all periods above 10%."""
        metric = GrowthMetric(name="Revenue", year_1=15, year_3=12, year_5=11, year_10=13)
        assert metric.consistent_above_10 is True

    def test_consistent_above_10_one_fails(self) -> None:
        """Test consistency fails when one period below 10%."""
        metric = GrowthMetric(name="Revenue", year_1=15, year_3=12, year_5=8, year_10=13)
        assert metric.consistent_above_10 is False

    def test_consistent_above_10_partial_data(self) -> None:
        """Test consistency with partial data."""
        metric = GrowthMetric(name="Revenue", year_1=15, year_5=12)
        assert metric.consistent_above_10 is True

    def test_consistent_above_10_no_data(self) -> None:
        """Test consistency returns False with no data."""
        metric = GrowthMetric(name="Revenue")
        assert metric.consistent_above_10 is False


class TestBigFourGrowth:
    """Tests for Big Four growth analysis."""

    def test_consistent_count(self) -> None:
        """Test counting consistent growth metrics."""
        growth = BigFourGrowth(
            revenue=GrowthMetric(name="Revenue", year_1=15, year_5=12),
            eps=GrowthMetric(name="EPS", year_1=20, year_5=18),
            book_value=GrowthMetric(name="BV", year_1=5, year_5=8),  # Fails
            fcf=GrowthMetric(name="FCF", year_1=25, year_5=22),
        )
        assert growth.consistent_count == 3

    def test_consistency_rating_excellent(self) -> None:
        """Test excellent rating when all 4 consistent."""
        growth = BigFourGrowth(
            revenue=GrowthMetric(name="Revenue", year_1=15, year_5=12),
            eps=GrowthMetric(name="EPS", year_1=20, year_5=18),
            book_value=GrowthMetric(name="BV", year_1=15, year_5=14),
            fcf=GrowthMetric(name="FCF", year_1=25, year_5=22),
        )
        assert growth.consistency_rating == "Excellent"

    def test_consistency_rating_good(self) -> None:
        """Test good rating when 3 consistent."""
        growth = BigFourGrowth(
            revenue=GrowthMetric(name="Revenue", year_1=15, year_5=12),
            eps=GrowthMetric(name="EPS", year_1=20, year_5=18),
            book_value=GrowthMetric(name="BV", year_1=5, year_5=8),  # Fails
            fcf=GrowthMetric(name="FCF", year_1=25, year_5=22),
        )
        assert growth.consistency_rating == "Good"

    def test_conservative_growth_rate(self) -> None:
        """Test conservative growth rate uses minimum."""
        growth = BigFourGrowth(
            revenue=GrowthMetric(name="Revenue", year_5=12),
            eps=GrowthMetric(name="EPS", year_5=8),  # Lowest positive
            book_value=GrowthMetric(name="BV", year_5=15),
            fcf=GrowthMetric(name="FCF", year_5=20),
        )
        assert growth.conservative_growth_rate == 8

    def test_conservative_growth_rate_ignores_negative(self) -> None:
        """Test conservative growth rate ignores negative values."""
        growth = BigFourGrowth(
            revenue=GrowthMetric(name="Revenue", year_5=12),
            eps=GrowthMetric(name="EPS", year_5=-5),  # Negative, ignored
            book_value=GrowthMetric(name="BV", year_5=15),
            fcf=GrowthMetric(name="FCF", year_5=20),
        )
        assert growth.conservative_growth_rate == 12


class TestBVGrowthCalculation:
    """Tests for book value growth CAGR calculation."""

    def test_calculate_bv_growth_5_year(self) -> None:
        """Test 5-year BV growth calculation."""
        financials = FinancialStatements(
            symbol="TEST",
            periods=[
                FinancialPeriod(period="2024", book_value_per_share=100.0),
                FinancialPeriod(period="2023", book_value_per_share=90.0),
                FinancialPeriod(period="2022", book_value_per_share=80.0),
                FinancialPeriod(period="2021", book_value_per_share=70.0),
                FinancialPeriod(period="2020", book_value_per_share=60.0),
                FinancialPeriod(period="2019", book_value_per_share=50.0),  # 5 years ago
            ],
        )
        bv_growth = _calculate_bv_growth(financials)
        # 100/50 = 2.0, 2^(1/5) - 1 = 0.1487 = ~14.87%
        assert bv_growth.year_5 is not None
        assert 14 < bv_growth.year_5 < 15

    def test_calculate_bv_growth_insufficient_data(self) -> None:
        """Test BV growth with insufficient data."""
        financials = FinancialStatements(
            symbol="TEST",
            periods=[
                FinancialPeriod(period="2024", book_value_per_share=100.0),
            ],
        )
        bv_growth = _calculate_bv_growth(financials)
        assert bv_growth.year_1 is None
        assert bv_growth.year_5 is None


class TestRule1Valuation:
    """Tests for Rule #1 sticker price calculation."""

    def test_calculate_rule1_full(self) -> None:
        """Test full Rule #1 calculation."""
        keyratios = KeyRatios(
            symbol="TEST",
            per_share=PerShareData(eps_ttm=5.0),
        )
        growth = BigFourGrowth(
            revenue=GrowthMetric(name="Revenue", year_5=15),
            eps=GrowthMetric(name="EPS", year_5=12),
            book_value=GrowthMetric(name="BV", year_5=10),  # Lowest
            fcf=GrowthMetric(name="FCF", year_5=18),
        )

        rule1 = _calculate_rule1(keyratios, growth)

        assert rule1.eps_ttm == 5.0
        assert rule1.growth_rate == 10.0  # Conservative rate
        assert rule1.future_pe == 20.0  # 2 * 10%
        assert rule1.future_eps_10y is not None
        assert rule1.sticker_price is not None
        assert rule1.buy_price is not None
        # Buy price should be 50% of sticker price
        assert rule1.buy_price == pytest.approx(rule1.sticker_price * 0.5, rel=0.01)

    def test_calculate_rule1_caps_pe_at_40(self) -> None:
        """Test that future P/E is capped at 40."""
        keyratios = KeyRatios(
            symbol="TEST",
            per_share=PerShareData(eps_ttm=5.0),
        )
        growth = BigFourGrowth(
            eps=GrowthMetric(name="EPS", year_5=25),  # Would give P/E of 50
        )

        rule1 = _calculate_rule1(keyratios, growth)
        assert rule1.future_pe == 40.0  # Capped


class TestValuationAnalysis:
    """Tests for valuation analysis."""

    def test_gf_value_discount_undervalued(self) -> None:
        """Test discount calculation for undervalued stock."""
        valuation = ValuationAnalysis(current_price=80.0, gf_value=100.0)
        assert valuation.gf_value_discount == 20.0  # 20% discount

    def test_gf_value_discount_overvalued(self) -> None:
        """Test discount calculation for overvalued stock."""
        valuation = ValuationAnalysis(current_price=120.0, gf_value=100.0)
        assert valuation.gf_value_discount == -20.0  # 20% premium

    def test_verdict_undervalued(self) -> None:
        """Test undervalued verdict."""
        valuation = ValuationAnalysis(current_price=70.0, gf_value=100.0)
        assert valuation.verdict == "Undervalued"

    def test_verdict_overvalued(self) -> None:
        """Test overvalued verdict."""
        valuation = ValuationAnalysis(current_price=130.0, gf_value=100.0)
        assert valuation.verdict == "Overvalued"

    def test_verdict_fairly_valued(self) -> None:
        """Test fairly valued verdict."""
        valuation = ValuationAnalysis(current_price=95.0, gf_value=100.0)
        assert valuation.verdict == "Fairly Valued"


class TestSummaryScore:
    """Tests for weighted overall score calculation."""

    def test_overall_score_perfect(self) -> None:
        """Test perfect score calculation."""
        summary = SummaryScore(
            qgarp_screen_score=5,
            quality_score=10,
            financial_strength_pass=True,
            growth_consistency_score=4,
            profitability_score=10,
            valuation_score=10,
        )
        assert summary.overall_score == 100

    def test_overall_score_zero(self) -> None:
        """Test zero score calculation."""
        summary = SummaryScore(
            qgarp_screen_score=0,
            quality_score=0,
            financial_strength_pass=False,
            growth_consistency_score=0,
            profitability_score=0,
            valuation_score=0,
        )
        assert summary.overall_score == 0

    def test_overall_score_mixed(self) -> None:
        """Test mixed score calculation."""
        summary = SummaryScore(
            qgarp_screen_score=4,  # 4/5 = 80% * 20 = 16
            quality_score=8,  # 8/10 = 80% * 15 = 12
            financial_strength_pass=True,  # 20
            growth_consistency_score=2,  # 2/4 = 50% * 15 = 7.5
            profitability_score=6,  # 6/10 = 60% * 10 = 6
            valuation_score=7,  # 7/10 = 70% * 20 = 14
        )
        # 16 + 12 + 20 + 7.5 + 6 + 14 = 75.5 -> 76
        assert summary.overall_score == 76


class TestGateDecision:
    """Tests for gate decision logic."""

    def test_gate_proceed(self) -> None:
        """Test PROCEED gate decision."""
        # Create minimal test data that leads to PROCEED
        summary = StockSummary(
            symbol="TEST",
            general=GeneralInfo(company_name="Test Co"),
            quality=SummaryQualityScores(gf_score=80, financial_strength=8),
            valuation=ValuationMetrics(),
            price=PriceInfo(current=100.0),
        )
        keyratios = KeyRatios(
            symbol="TEST",
            profitability=ProfitabilityRatios(roic=15.0),
            growth=GrowthRatios(
                revenue_growth_5y=12.0,
                eps_growth_5y=14.0,
                revenue_growth_1y=10.0,
                eps_growth_1y=12.0,
            ),
            solvency=SolvencyRatios(debt_to_equity=0.3, interest_coverage=10.0),
            liquidity=LiquidityRatios(current_ratio=2.0),
            valuation=ValuationRatios(pe_ratio=25.0),
            per_share=PerShareData(eps_ttm=5.0),
        )
        financials = FinancialStatements(
            symbol="TEST",
            periods=[
                FinancialPeriod(period="2024", book_value_per_share=100.0),
                FinancialPeriod(period="2023", book_value_per_share=90.0),
                FinancialPeriod(period="2022", book_value_per_share=81.0),
                FinancialPeriod(period="2021", book_value_per_share=73.0),
                FinancialPeriod(period="2020", book_value_per_share=66.0),
                FinancialPeriod(period="2019", book_value_per_share=60.0),
            ],
        )

        analysis = compute_qgarp_analysis("TEST", summary, keyratios, financials)

        # Should meet all criteria for PROCEED
        assert analysis.decision.qgarp_passed is True
        assert analysis.decision.financial_passed is True
        assert analysis.decision.quality_passed is True
        assert analysis.decision.gate_decision == GateDecision.PROCEED

    def test_gate_watchlist(self) -> None:
        """Test WATCHLIST gate decision (passes screen but fails quality)."""
        summary = StockSummary(
            symbol="TEST",
            general=GeneralInfo(company_name="Test Co"),
            quality=SummaryQualityScores(gf_score=60),  # Below 70
            valuation=ValuationMetrics(),
            price=PriceInfo(current=100.0),
        )
        keyratios = KeyRatios(
            symbol="TEST",
            profitability=ProfitabilityRatios(roic=15.0),
            growth=GrowthRatios(revenue_growth_5y=12.0, eps_growth_5y=14.0),
            solvency=SolvencyRatios(debt_to_equity=0.3, interest_coverage=10.0),
            liquidity=LiquidityRatios(current_ratio=2.0),
            valuation=ValuationRatios(pe_ratio=25.0),
        )
        financials = FinancialStatements(symbol="TEST", periods=[])

        analysis = compute_qgarp_analysis("TEST", summary, keyratios, financials)

        assert analysis.decision.qgarp_passed is True
        assert analysis.decision.financial_passed is True
        assert analysis.decision.quality_passed is False
        assert analysis.decision.gate_decision == GateDecision.WATCHLIST

    def test_gate_discard(self) -> None:
        """Test DISCARD gate decision (fails screen)."""
        summary = StockSummary(
            symbol="TEST",
            general=GeneralInfo(company_name="Test Co"),
            quality=SummaryQualityScores(gf_score=80),
            valuation=ValuationMetrics(),
            price=PriceInfo(current=100.0),
        )
        keyratios = KeyRatios(
            symbol="TEST",
            profitability=ProfitabilityRatios(roic=5.0),  # Fails ROIC
            growth=GrowthRatios(revenue_growth_5y=5.0, eps_growth_5y=5.0),  # Fails growth
            solvency=SolvencyRatios(debt_to_equity=1.0, interest_coverage=1.5),  # Fails D/E
            liquidity=LiquidityRatios(current_ratio=1.0),
            valuation=ValuationRatios(pe_ratio=50.0),  # Fails P/E
        )
        financials = FinancialStatements(symbol="TEST", periods=[])

        analysis = compute_qgarp_analysis("TEST", summary, keyratios, financials)

        assert analysis.decision.qgarp_passed is False
        assert analysis.decision.gate_decision == GateDecision.DISCARD
