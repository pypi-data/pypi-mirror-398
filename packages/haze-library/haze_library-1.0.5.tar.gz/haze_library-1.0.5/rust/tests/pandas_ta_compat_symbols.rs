use haze_library::indicators::pandas_ta_compat as p;

#[test]
fn pandas_ta_compat_symbols_exist() {
    // candle
    let _ = p::cdl_pattern;
    let _ = p::cdl_z;
    let _ = p::ha;

    // cycle
    let _ = p::ebsw;
    let _ = p::reflex;

    // momentum
    let _ = p::ao;
    let _ = p::apo;
    let _ = p::bias;
    let _ = p::bop;
    let _ = p::brar;
    let _ = p::cci;
    let _ = p::cfo;
    let _ = p::cg;
    let _ = p::cmo;
    let _ = p::coppock;
    let _ = p::crsi;
    let _ = p::cti;
    let _ = p::er;
    let _ = p::eri;
    let _ = p::exhc;
    let _ = p::fisher;
    let _ = p::inertia;
    let _ = p::kdj;
    let _ = p::kst;
    let _ = p::macd;
    let _ = p::mom;
    let _ = p::pgo;
    let _ = p::ppo;
    let _ = p::psl;
    let _ = p::qqe;
    let _ = p::roc;
    let _ = p::rsi;
    let _ = p::rsx;
    let _ = p::rvgi;
    let _ = p::slope;
    let _ = p::smc;
    let _ = p::smi;
    let _ = p::squeeze;
    let _ = p::squeeze_pro;
    let _ = p::stc;
    let _ = p::stoch;
    let _ = p::stochf;
    let _ = p::stochrsi;
    let _ = p::tmo;
    let _ = p::trix;
    let _ = p::tsi;
    let _ = p::uo;
    let _ = p::willr;

    // overlap
    let _ = p::alligator;
    let _ = p::alma;
    let _ = p::dema;
    let _ = p::ema;
    let _ = p::fwma;
    let _ = p::hilo;
    let _ = p::hl2;
    let _ = p::hlc3;
    let _ = p::hma;
    let _ = p::hwma;
    let _ = p::ichimoku;
    let _ = p::jma;
    let _ = p::kama;
    let _ = p::linreg;
    let _ = p::mama;
    let _ = p::mcgd;
    let _ = p::midpoint;
    let _ = p::midprice;
    let _ = p::ohlc4;
    let _ = p::pivots;
    let _ = p::pwma;
    let _ = p::rma;
    let _ = p::sinwma;
    let _ = p::sma;
    let _ = p::smma;
    let _ = p::ssf;
    let _ = p::ssf3;
    let _ = p::supertrend;
    let _ = p::swma;
    let _ = p::t3;
    let _ = p::tema;
    let _ = p::trima;
    let _ = p::vidya;
    let _ = p::wcp;
    let _ = p::wma;
    let _ = p::zlma;

    // performance
    let _ = p::log_return;
    let _ = p::percent_return;

    // statistics
    let _ = p::entropy;
    let _ = p::kurtosis;
    let _ = p::mad;
    let _ = p::median;
    let _ = p::quantile;
    let _ = p::skew;
    let _ = p::stdev;
    let _ = p::tos_stdevall;
    let _ = p::variance;
    let _ = p::zscore;

    // trend
    let _ = p::adx;
    let _ = p::alphatrend;
    let _ = p::amat;
    let _ = p::aroon;
    let _ = p::chop;
    let _ = p::cksp;
    let _ = p::decay;
    let _ = p::decreasing;
    let _ = p::dpo;
    let _ = p::ht_trendline;
    let _ = p::increasing;
    let _ = p::long_run;
    let _ = p::psar;
    let _ = p::qstick;
    let _ = p::rwi;
    let _ = p::short_run;
    let _ = p::trendflex;
    let _ = p::vhf;
    let _ = p::vortex;
    let _ = p::zigzag;

    // volatility
    let _ = p::aberration;
    let _ = p::accbands;
    let _ = p::atr;
    let _ = p::atrts;
    let _ = p::bbands;
    let _ = p::chandelier_exit;
    let _ = p::donchian;
    let _ = p::hwc;
    let _ = p::kc;
    let _ = p::massi;
    let _ = p::natr;
    let _ = p::pdist;
    let _ = p::rvi;
    let _ = p::thermo;
    let _ = p::true_range;
    let _ = p::ui;

    // volume
    let _ = p::ad;
    let _ = p::adosc;
    let _ = p::aobv;
    let _ = p::cmf;
    let _ = p::efi;
    let _ = p::eom;
    let _ = p::kvo;
    let _ = p::mfi;
    let _ = p::nvi;
    let _ = p::obv;
    let _ = p::pvi;
    let _ = p::pvo;
    let _ = p::pvol;
    let _ = p::pvr;
    let _ = p::pvt;
    let _ = p::tsv;
    let _ = p::vhm;
    let _ = p::vwap;
    let _ = p::vwma;
}
