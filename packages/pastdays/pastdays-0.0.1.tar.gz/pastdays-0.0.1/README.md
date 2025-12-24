# pastdays

> Find **past market days similar to today** and see what actually happened next.

`pastdays` is a Python library that compares **current partial market data**
with **historical data** to identify **similar past days** and analyze
their outcomes.

It does **not predict**, **does not trade**, and **does not generate signals**.
It simply answers one question:

> “When the market looked like this before, what happened afterwards?”

---

## ✨ Why this library exists

Most backtests lie because they assume:
    - perfect execution
    - known future
    - curve-fitted parameters

Traders, however, think differently:

    > “Have I seen this kind of day before?”

    `pastdays` is built around that mindset.

---

## 🧠 What it does (v0)

    - Accepts **user-provided historical data**
    - Accepts **current-day partial data**
    - Extracts simple, explainable features
    - Finds **K most similar historical days**
    - Reports **what happened next** on those days

No machine learning. No black box.

---

## 📦 Installation

    pip install pastdays

