# ADF 테스트 - 정상성 확인용
from statsmodels.tsa.stattools import adfuller
# 시계열 분해 패키지
from statsmodels.tsa.seasonal import seasonal_decompose
# ACF, PACF 테스트
from statsmodels.tsa.stattools import acf, pacf
# ACF, PACF 시각화 기능
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
# ARIMA
from statsmodels.tsa.arima.model import ARIMA
# 데이터 핸들
from pandas import DataFrame, to_datetime
# 시각화 관련
from matplotlib import pyplot as plt
# NumPy
import numpy as np


# -------------------------------------------------------------


def my_time_index(df, field, freq=None, format=None):
    df2 = df.copy()

    if format:
        df2[field] = to_datetime(df[field], format=format)

    df2.set_index(field, inplace=True)

    if freq is not None:
        df2 = df2.asfreq(freq)

    return df2


# -------------------------------------------------------------


def my_diff(df, yname):
    diff_df = df.copy()
    diff_count = 0   # 몇 번까지 차분을 수행했는지 count
    result = []      # 결과를 저장할 빈 리스트

    while True:
        ar = adfuller(diff_df[yname])
        ar_dict = {
            '차수': diff_count,
            'ADF Statistic': ar[0],
            'p-value': ar[1],
            'result' : True if ar[1] <= 0.05 else False
        }

        # 리스트에 정상성 검사 결과를 저장
        result.append(ar_dict)

        # 정상성 충족이라면 반복 중단
        if ar_dict['result']:
            #break
            return DataFrame(result), diff_df

        # 정상성이 충족되지 않았다면 차분 수행 후 다시 수행
        diff_count += 1
        diff_df = diff_df.diff().dropna()


# -------------------------------------------------------------


def my_acf_pacf(df, yname):
    my_dpi = 200

    diff_df = df.copy()

    # -----------------------
    # ACF
    # -----------------------
    # 1) ACF 계산
    acf_vals = acf(diff_df[yname])
    threshold = 2 / np.sqrt(len(diff_df[yname]))

    # 2) 결과표 생성
    df_acf = DataFrame({
        "lag": np.arange(len(acf_vals)),
        "acf": acf_vals,
    })

    # 3) 유의성 판단
    df_acf["abs_acf"] = df_acf["acf"].abs()
    df_acf["significant"] = df_acf["abs_acf"] > threshold

    # 4) 보기 좋게 정리
    df_acf["acf"] = df_acf["acf"].round(3)
    df_acf["abs_acf"] = df_acf["abs_acf"].round(3)
    df_acf["threshold"] = round(threshold, 3)

    # 5) lag=0 제외 (판정용)
    df_acf_result = df_acf.query("lag > 0").reset_index(drop=True)

    # 6) 연속 유의 구간 계산
    df_acf_result["prev_significant"] = df_acf_result["significant"].shift(1)

    df_acf_result["cut_candidate"] = (
        (df_acf_result["prev_significant"] == True) &
        (df_acf_result["significant"] == False)
    )

    # 7) q 후보
    q_candidate = (
        df_acf_result
        .loc[df_acf_result["cut_candidate"], "lag"]
        .min() - 1
    )


    # -----------------------
    # PACF
    # -----------------------
    # 1) PACF 계산
    pacf_vals = pacf(diff_df[yname])
    threshold = 2 / np.sqrt(len(diff_df[yname]))

    # 2) 결과표 생성
    df_pacf = DataFrame({
        "lag": np.arange(len(pacf_vals)),
        "pacf": pacf_vals,
    })

    # 3) 유의성 판단
    df_pacf["abs_pacf"] = df_pacf["pacf"].abs()
    df_pacf["significant"] = df_pacf["abs_pacf"] > threshold

    # 4) 보기 좋게 정리
    df_pacf["pacf"] = df_pacf["pacf"].round(3)
    df_pacf["abs_pacf"] = df_pacf["abs_pacf"].round(3)
    df_pacf["threshold"] = round(threshold, 3)

    # 5) lag=0 제외
    df_pacf_result = df_pacf.query("lag > 0").reset_index(drop=True)

    # 6) 연속 유의구간 계산
    df_pacf_result["prev_significant"] = df_pacf_result["significant"].shift(1)

    df_pacf_result["cut_candidate"] = (
        (df_pacf_result["prev_significant"] == True) &
        (df_pacf_result["significant"] == False)
    )

    # 7. p값 후보
    p_candidate = (
        df_pacf_result
        .loc[df_pacf_result["cut_candidate"], "lag"]
        .min() - 1
    )


    # -----------------------
    # 서브플롯 시각화
    # -----------------------
    # 1) 그래프 초기화
    width_px  = 2000                    # 그래프 가로 크기
    height_px = 1500                    # 그래프 세로 크기
    rows = 2                            # 그래프 행 수
    cols = 1                            # 그래프 열 수
    figsize = (width_px / my_dpi, height_px / my_dpi)

    # ax 객체가 행,열 수에 따라서 리스트가 된다.
    fig, ax = plt.subplots(rows, cols, figsize=figsize, dpi=my_dpi)


    # 2-1) ACF Plot 그리기 -> ax파라미터 필수
    plot_acf(diff_df[yname], ax=ax[0])

    # 2-2) MA(q) 후보 시각화
    ax[0].axvline(
        x=q_candidate,
        linestyle="--",
        linewidth=1.5,
        alpha=0.8,
        color='red'
    )
    ax[0].text(
        q_candidate + 0.1,
        ax[0].get_ylim()[1] * 0.9,
        f"MA(q) candidate = {q_candidate}",
        fontsize=9,
        verticalalignment="top"
    )

    # 2-3) 그래프 꾸미기
    ax[0].set_title("ACF Plot", fontsize=12, pad=8)
    ax[0].set_xlabel("Lag", fontsize=8, labelpad=5)
    ax[0].set_ylabel("Autocorrelation", fontsize=8, labelpad=5)
    ax[0].grid(True, alpha=0.3)            # 배경 격자 표시


    # 3-1) PACF Plot 그리기
    plot_pacf(diff_df[yname], ax=ax[1])

    # 3-2) AR(p) 후보 시각화
    ax[1].axvline(
        x=p_candidate,
        linestyle="--",
        linewidth=1.5,
        alpha=0.8,
        color="red"
    )
    ax[1].text(
        p_candidate + 0.1,
        ax[1].get_ylim()[1] * 0.9,
        f"AR(p) candidate = {p_candidate}",
        fontsize=9,
        verticalalignment="top"
    )

    # 3-3) 그래프 꾸미기
    ax[1].set_title("PACF Plot", fontsize=12, pad=8)
    ax[1].set_xlabel("Lag", fontsize=8, labelpad=5)
    ax[1].set_ylabel("Partial Autocorrelation", fontsize=8, labelpad=5)
    ax[1].grid(True, alpha=0.3)

    # 4) 출력
    plt.tight_layout()      # 여백 제거
    plt.show()              # 그래프 화면 출력
    plt.close()             # 그래프 작업 종료

    return p_candidate, q_candidate


# -------------------------------------------------------------


def my_arima(df, yname, p, d, q, s = None):

    p = 0 if np.isnan(p) else p
    d = 0 if np.isnan(d) else d
    q = 0 if np.isnan(q) else q
    s = 0 if np.isnan(s) else s

    results = []  # 결과 저장용

    for x in range(0, p+1):
        for y in range(0, d+1):
            for z in range(0, q+1):
                try:
                    if not s:
                        print(f"p={x}, d={y}, q={z}")
                        model = ARIMA(df[yname], order=(x, y, z))
                    else:
                        print(f"p={x}, d={y}, q={z}, s={s}")
                        model = ARIMA(df[yname], order=(x, y, z), seasonal_order=(x, y, z, s))

                    fit = model.fit()

                    if not fit.mle_retvals['converged']:
                        continue   # ❗ 수렴 실패 모델 제외

                    results.append({
                        'p': x,
                        'd': y,
                        'q': z,
                        'AIC': fit.aic,
                        'BIC': fit.bic,
                        'Best': False
                    })
                except Exception as e:
                    # 수렴 실패 / 모형 오류는 건너뜀
                    continue

    df_results = DataFrame(results)
    best_model = df_results.sort_values(['BIC', 'AIC']).iloc[0]

    # 최종 모델 학습
    best_order = (
        int(best_model['p']),
        int(best_model['d']),
        int(best_model['q'])
    )

    s_best_order = (
        int(best_model['p']),
        int(best_model['d']),
        int(best_model['q']),
        12
    )

    fit = ARIMA(df[yname], order=best_order, seasonal_order=s_best_order).fit()

    return df_results, fit


# -------------------------------------------------------------


def my_arima_report(fit, threshold=0.05):
    """
    SARIMAXResults 객체(fit)와 원본 데이터(data)를 받아
    모형 적합도 표(cdf),
    계수 요약 표(rdf),
    모형 요약 문장(result_report),
    모형 판정 문장(model_report),
    계수별 해석 문장(variable_reports)를 반환한다.
    """

    # -----------------------------
    # 모형 적합도 요약
    # -----------------------------
    cdf = DataFrame({
        "Log Likelihood": [fit.llf],
        "AIC": [fit.aic],
        "BIC": [fit.bic],
        "HQIC": [fit.hqic],
        "관측치 수": [fit.nobs]
    })

    # -----------------------------
    # 계수 테이블 구성
    # -----------------------------
    params = fit.params
    bse = fit.bse
    zvals = params / bse
    pvals = fit.pvalues
    conf = fit.conf_int()

    rows = []
    for name in params.index:
        p = pvals[name]
        stars = (
            "***" if p < 0.001 else
            "**" if p < 0.01 else
            "*" if p < 0.05 else
            ""
        )

        rows.append({
            "변수": name,
            "계수": params[name],
            "표준오차": bse[name],
            "z": f"{zvals[name]:.3f}{stars}",
            "p-value": p,
            "CI_lower": conf.loc[name, 0],
            "CI_upper": conf.loc[name, 1]
        })

    rdf = DataFrame(rows)

    # -----------------------------
    # 모형 요약 문장
    # -----------------------------
    result_report = (
        f"Log Likelihood = {fit.llf:.3f}, "
        f"AIC = {fit.aic:.3f}, "
        f"BIC = {fit.bic:.3f}."
    )

    # -----------------------------
    # 모형 판정 문장
    # -----------------------------
    lb = fit.test_serial_correlation(method="ljungbox")
    # statsmodels 버전마다 pvalue값의 인덱스가 상이함
    lb_pvalue = lb[0][1][-1]

    model_report = (
        f"ARIMA{fit.model.order}×{fit.model.seasonal_order} 모형을 적합한 결과, "
        f"AIC {fit.aic:.3f}, BIC {fit.bic:.3f}로 나타났으며 "
    )

    if lb_pvalue >= threshold:
        model_report += (
            "잔차들 사이에 특별한 시간적 패턴은 관찰되지 않음을 통계적으로 확인하였다."
            "(잔차의 자기상관은 Ljung-Box 검정에서 유의하지 않았다)"
        )
    else:
        model_report += (
            "잔차들 사이에 시간적 패턴이 남아 있는 것으로 나타났으며, "
            "모형이 충분히 설명하지 못했을 가능성이 있다."
            "(잔차의 자기상관이 Ljung-Box 검정에서 통계적으로 유의하다)"
        )

    # -----------------------------
    # 계수별 해석 문장 (시계열 특성 설명 포함)
    # -----------------------------
    variable_reports = []

    for _, row in rdf.iterrows():
        name = row['변수']

        if name == "const":
            continue

        coef = row['계수']
        pval = row['p-value']

        # --- 변수 유형 해석 ---
        if name.startswith("ar.S"):
            meaning = "한 시즌 전 같은 시점의 값이 현재 값에 미치는 영향"
        elif name.startswith("ma.S"):
            meaning = "한 시즌 전 같은 시점에서 발생한 예측 오차가 현재에 남긴 영향"
        elif name.startswith("ar."):
            meaning = "직전 시점의 값이 현재 값에 미치는 영향"
        elif name.startswith("ma."):
            meaning = "직전 시점에서 발생한 예측 오차가 현재에 남긴 영향"
        elif name == "const":
            meaning = "전체 시계열의 기본 수준"
        else:
            meaning = "시계열의 특정 구조적 요소"

        # --- 방향 해석 ---
        if coef > 0:
            direction = "값을 높이는 방향"
        elif coef < 0:
            direction = "값을 낮추는 방향"
        else:
            direction = "뚜렷한 방향성은 없음"

        # --- 통계적 유의성 ---
        if pval < threshold:
            stat_text = "통계적으로 의미가 있다"
            plain_text = "우연이 아니라 반복되는 패턴일 가능성이 높다"
        else:
            stat_text = "통계적으로 뚜렷하지 않다"
            plain_text = "우연에 의해 나타났을 가능성을 배제하기 어렵다"

        variable_reports.append(
            f"{name}의 계수는 {coef:.3f}으로 {stat_text} (p {'<' if pval < threshold else '>'} {threshold}). "
            f"({meaning}로, 이 영향은 현재 값의 흐름을 {direction} 작용하며 "
            f"{plain_text})"
        )


    return cdf, rdf, result_report, model_report, variable_reports