import streamlit as st
import pandas as pd

st.set_page_config(page_title="Calculadoras Financeiras", page_icon="📈", layout="centered")


def brl(v: float) -> str:
    s = f"{v:,.2f}"
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"R$ {s}"


def monthly_rate_from(rate_input: float, period: str) -> float:
    r = rate_input / 100
    if period == "Ao ano":
        return (1 + r) ** (1 / 12) - 1
    return r


def ir_bracket_for(months: int):
    if months <= 6:
        return {"rate": 0.225, "label": "até 180 dias", "name": "22,5%"}
    if months <= 12:
        return {"rate": 0.20, "label": "de 181 a 360 dias", "name": "20%"}
    if months <= 24:
        return {"rate": 0.175, "label": "de 361 a 720 dias", "name": "17,5%"}
    return {"rate": 0.15, "label": "acima de 720 dias", "name": "15%"}


def build_yearly_table(yearly: list) -> pd.DataFrame:
    rows = []
    prev_invested, prev_balance = 0.0, 0.0
    for d in yearly:
        invested_this_year = d["invested"] - prev_invested
        total_interest = d["balance"] - d["invested"]
        rows.append({
            "Ano": d["year"],
            "Investido no ano": brl(invested_this_year),
            "Total investido": brl(d["invested"]),
            "Total em juros": brl(total_interest),
            "Acumulado": brl(d["balance"]),
        })
        prev_invested, prev_balance = d["invested"], d["balance"]
    return pd.DataFrame(rows)


def chart_df(yearly: list) -> pd.DataFrame:
    data = [d for d in yearly if d["year"] > 0]
    return pd.DataFrame({
        "Ano": [d["year"] for d in data],
        "Total investido": [d["invested"] for d in data],
        "Valor acumulado": [d["balance"] for d in data],
    }).set_index("Ano")


def go_to(page: str):
    st.session_state.page = page


if "page" not in st.session_state:
    st.session_state.page = "home"

# ----------------------------------------------------------------------------
# HOME
# ----------------------------------------------------------------------------

def render_home():
    st.title(" Calculadoras Financeiras")

    col1 = st.container(border=True)
    with col1:
        st.subheader("Primeiro Milhão")
        st.write("Quanto tempo falta para chegar à sua meta, dado o que você já tem, aporta e rende.")
        st.button("Abrir calculadora", key="btn_milhao", on_click=go_to, args=("milhao",), use_container_width=True)

    col2 = st.container(border=True)
    with col2:
        st.subheader("Juros Compostos")
        st.write("Quanto um valor inicial e aportes mensais podem virar ao longo do tempo.")
        st.button("Abrir calculadora", key="btn_juros", on_click=go_to, args=("juros",), use_container_width=True)

    col3 = st.container(border=True)
    with col3:
        st.subheader("Imposto de Renda")
        st.write("Quanto do rendimento vai para o IR, pela tabela regressiva, e quanto sobra líquido.")
        st.button("Abrir calculadora", key="btn_imposto", on_click=go_to, args=("imposto",), use_container_width=True)




def render_milhao():
    st.button("← Voltar", on_click=go_to, args=("home",))
    st.title("Primeiro Milhão")
    st.write(
        "Informe quanto você já tem, quanto consegue investir por mês e a taxa de juros esperada. "
        "Calculamos em quanto tempo você atinge sua meta."
    )

    col1, col2 = st.columns(2)
    goal = col1.number_input("Valor da meta (R$)", min_value=0.0, value=1_000_000.0, step=1000.0)
    initial = col2.number_input("Quanto já tem investido (R$)", min_value=0.0, value=1000.0, step=100.0)

    col3, col4, col5 = st.columns([2, 1, 2])
    rate_input = col3.number_input("Taxa de juros (%)", min_value=0.0, value=12.0, step=0.1)
    rate_period = col4.selectbox("Período", ["Ao ano", "Ao mês"], key="m_period")
    monthly = col5.number_input("Aporte mensal (R$)", min_value=0.0, value=300.0, step=50.0)

    if st.button("Calcular", type="primary", key="calc_milhao"):
        if goal <= 0:
            st.error("A meta precisa ser maior que zero.")
            return

        i = monthly_rate_from(rate_input, rate_period)
        balance = initial
        invested = initial
        months = 0
        max_months = 1200  # cap at 100 years
        yearly = [{"year": 0, "invested": invested, "balance": balance}]

        if balance < goal:
            while balance < goal and months < max_months:
                balance = balance * (1 + i) + monthly
                invested += monthly
                months += 1
                if months % 12 == 0:
                    yearly.append({"year": months // 12, "invested": invested, "balance": balance})
        if months % 12 != 0 and months < max_months:
            yearly.append({"year": round(months / 12, 1), "invested": invested, "balance": balance})

        st.write("---")
        if balance < goal:
            st.warning(
                f"Com esses valores, a meta de **{brl(goal)}** não é alcançada em 100 anos. "
                "Tente aumentar o aporte mensal ou a taxa de juros."
            )
        else:
            years = months // 12
            rem = months % 12
            parts = []
            if years > 0:
                parts.append(f"{years} {'ano' if years == 1 else 'anos'}")
            if rem > 0:
                parts.append(f"{rem} {'mês' if rem == 1 else 'meses'}")
            time_str = " e ".join(parts) if parts else "menos de 1 mês"
            st.success(f"Você atinge sua meta de **{brl(goal)}** em **{time_str}**.")

            m1, m2, m3 = st.columns(3)
            m1.metric("Tempo até a meta", time_str)
            m2.metric("Total investido", brl(invested))
            m3.metric("Total em juros", brl(max(0.0, balance - invested)))
            st.caption(f"Valor final projetado: {brl(balance)}.")

        st.write("#### Evolução do patrimônio")
        st.bar_chart(chart_df(yearly))

        st.write("#### Tabela ano a ano")
        st.dataframe(build_yearly_table(yearly), use_container_width=True, hide_index=True)


def render_juros():
    st.button("← Voltar", on_click=go_to, args=("home",))
    st.title("📊 Juros Compostos")
    st.write(
        "Informe um valor inicial, uma taxa de juros e um prazo. Se quiser, some aportes mensais "
        "para ver o efeito de investir com constância."
    )

    c1, c2 = st.columns(2)
    initial = c1.number_input("Valor inicial (R$)", min_value=0.0, value=5000.0, step=100.0, key="j_initial")
    monthly = c2.number_input("Aporte mensal (R$)", min_value=0.0, value=200.0, step=50.0, key="j_monthly")

    c3, c4, c5, c6 = st.columns([2, 1, 2, 1])
    rate_input = c3.number_input("Taxa de juros (%)", min_value=0.0, value=12.0, step=0.1, key="j_rate")
    rate_period = c4.selectbox("Período", ["Ao ano", "Ao mês"], key="j_rate_period")
    time_input = c5.number_input("Prazo", min_value=0.0, value=10.0, step=1.0, key="j_time")
    time_period = c6.selectbox("Unidade", ["Anos", "Meses"], key="j_time_period")

    if st.button("Calcular", type="primary", key="calc_juros"):
        if time_input <= 0:
            st.error("O prazo precisa ser maior que zero.")
            return

        total_months = round(time_input * 12) if time_period == "Anos" else round(time_input)
        i = monthly_rate_from(rate_input, rate_period)

        balance = initial
        invested = initial
        yearly = [{"year": 0, "invested": invested, "balance": balance}]
        for m in range(1, total_months + 1):
            balance = balance * (1 + i) + monthly
            invested += monthly
            if m % 12 == 0:
                yearly.append({"year": m // 12, "invested": invested, "balance": balance})
        if total_months % 12 != 0:
            yearly.append({"year": round(total_months / 12, 1), "invested": invested, "balance": balance})

        interest = balance - invested
        unit_label = f"{time_input:g} {'ano' if (time_period == 'Anos' and time_input == 1) else ('anos' if time_period == 'Anos' else ('mês' if time_input == 1 else 'meses'))}"

        st.write("---")
        st.success(f"Em {unit_label}, seu dinheiro pode chegar a **{brl(balance)}**.")

        m1, m2, m3 = st.columns(3)
        m1.metric("Valor total final", brl(balance))
        m2.metric("Total investido", brl(invested))
        m3.metric("Total em juros", brl(interest))

        st.write("#### Evolução do patrimônio")
        st.bar_chart(chart_df(yearly))

        st.write("#### Tabela ano a ano")
        st.dataframe(build_yearly_table(yearly), use_container_width=True, hide_index=True)



def render_imposto():
    st.button("← Voltar", on_click=go_to, args=("home",))
    st.title("Imposto de Renda")
    st.write(
        "Simule um investimento de renda fixa tributado (CDB, Tesouro Direto, LC) e veja quanto o IR "
        "desconta no resgate, pela tabela regressiva."
    )

    c1, c2 = st.columns(2)
    initial = c1.number_input("Valor inicial (R$)", min_value=0.0, value=10000.0, step=100.0, key="i_initial")
    monthly = c2.number_input("Aporte mensal (R$)", min_value=0.0, value=0.0, step=50.0, key="i_monthly")

    c3, c4, c5, c6 = st.columns([2, 1, 2, 1])
    rate_input = c3.number_input("Taxa de juros (%)", min_value=0.0, value=12.0, step=0.1, key="i_rate")
    rate_period = c4.selectbox("Período", ["Ao ano", "Ao mês"], key="i_rate_period")
    time_input = c5.number_input("Prazo até o resgate", min_value=0.0, value=24.0, step=1.0, key="i_time")
    time_period = c6.selectbox("Unidade", ["Meses", "Anos"], key="i_time_period")

    if st.button("Calcular", type="primary", key="calc_imposto"):
        if time_input <= 0:
            st.error("O prazo precisa ser maior que zero.")
            return

        total_months = round(time_input * 12) if time_period == "Anos" else round(time_input)
        i = monthly_rate_from(rate_input, rate_period)

        balance = initial
        invested = initial
        for _ in range(total_months):
            balance = balance * (1 + i) + monthly
            invested += monthly

        gross_gain = balance - invested
        bracket = ir_bracket_for(total_months)
        tax = max(0.0, gross_gain) * bracket["rate"]
        net_gain = gross_gain - tax
        net_final = balance - tax

        st.write("---")
        st.info(
            f"Do rendimento bruto de **{brl(gross_gain)}**, {brl(tax)} vão para o Imposto de Renda "
            f"— sobram **{brl(net_final)}** líquidos."
        )

        m1, m2, m3 = st.columns(3)
        m1.metric("Rendimento bruto", brl(gross_gain))
        m2.metric("Alíquota de IR aplicada", bracket["name"])
        m3.metric("Imposto retido", brl(tax))

        m4, m5, m6 = st.columns(3)
        m4.metric("Total investido", brl(invested))
        m5.metric("Rendimento líquido", brl(net_gain))
        m6.metric("Valor final líquido", brl(net_final))

        st.caption(
            "Tabela regressiva de IR para renda fixa: até 180 dias, 22,5% · de 181 a 360 dias, 20% · "
            "de 361 a 720 dias, 17,5% · acima de 720 dias, 15%. O imposto incide apenas sobre o rendimento, "
            "nunca sobre o valor investido. Vale para ativos tributados como CDB e Tesouro Direto — LCI, LCA, "
            "CRI, CRA e debêntures incentivadas são isentos."
        )

        st.write("#### Tabela regressiva de IR")
        brackets = [
            {"label": "Até 180 dias", "name": "22,5%", "max_m": 6},
            {"label": "De 181 a 360 dias", "name": "20%", "max_m": 12},
            {"label": "De 361 a 720 dias", "name": "17,5%", "max_m": 24},
            {"label": "Acima de 720 dias", "name": "15%", "max_m": float("inf")},
        ]
        rows = []
        for b in brackets:
            is_current = bracket["name"] == b["name"]
            situacao = f"← seu prazo ({total_months} {'mês' if total_months == 1 else 'meses'})" if is_current else ""
            rows.append({"Prazo da aplicação": b["label"], "Alíquota": b["name"], "Situação": situacao})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


pages = {
    "home": render_home,
    "milhao": render_milhao,
    "juros": render_juros,
    "imposto": render_imposto,
}
pages.get(st.session_state.page, render_home)()
