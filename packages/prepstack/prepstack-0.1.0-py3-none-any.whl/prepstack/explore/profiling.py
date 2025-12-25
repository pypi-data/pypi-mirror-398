from .overview import dataset_overview, overview_insights
from .missing import missing_report, missing_insights
from .distributions import distribution_report, distribution_insights
from .correlations import correlation_report, correlation_insights

def auto_profile(df, guidance="off"):
    print("🔮 AUTO EDA PROFILE STARTED") if guidance == "on" else None
    print("--------------------------------------------------") if guidance == "on" else None

    ov = dataset_overview(df, guidance)
    ov_ins = overview_insights(df)

    ms = missing_report(df, guidance)
    ms_ins = missing_insights(ms)

    dist = distribution_report(df, guidance)
    dist_ins = distribution_insights(df)

    corr = correlation_report(df, guidance)
    corr_ins = correlation_insights(corr)

    if guidance == "on":
        print("\n💡 INSIGHTS SUMMARY")
        print("• OVERVIEW:", ov_ins)
        print("• MISSING:", ms_ins)
        print("• DISTRIBUTION:", dist_ins)
        print("• CORRELATION:", corr_ins)
        print("--------------------------------------------------")
        print("✨ Auto EDA Profile Complete.")

    return {
        "overview": ov,
        "overview_insights": ov_ins,
        "missing": ms,
        "missing_insights": ms_ins,
        "distribution": dist,
        "distribution_insights": dist_ins,
        "correlations": corr,
        "correlation_insights": corr_ins
    }
