"""The engine's own posted-date memory: earliest-wins, monotonic, per cycle."""

from intern_engine import observe


def test_ignores_records_without_posted_date_or_cycle():
    store = {
        "1": {"company": "Foo", "season": "2026 Graduates"},  # no posted_at
        "2": {"company": "Bar", "posted_at": "2026-01-01T00:00:00Z"},  # no season
    }
    out = observe.update_from_store(store, {"companies": {}})
    assert out["companies"] == {}


def test_is_monotonic_across_runs():
    prior = {
        "companies": {
            "stripe": {
                "name": "Stripe",
                "cycles": {"2026 Graduates": {"first_posted": "2026-06-30", "count": 1}},
            },
        }
    }
    # A later run where the role has closed/purged (empty store) must not erase it.
    out = observe.update_from_store({}, prior)
    assert out["companies"]["stripe"]["cycles"]["2026 Graduates"]["first_posted"] == "2026-06-30"


def test_normalizes_company_variants_together():
    store = {
        "1": {
            "company": "Stripe, Inc.",
            "season": "2026 Graduates",
            "posted_at": "2026-06-30T00:00:00Z",
        },
        "2": {"company": "Stripe", "season": "2026 Graduates", "posted_at": "2026-06-25T00:00:00Z"},
    }
    out = observe.update_from_store(store, {"companies": {}})
    keys = list(out["companies"])
    assert len(keys) == 1
    assert out["companies"][keys[0]]["cycles"]["2026 Graduates"]["first_posted"] == "2026-06-25"


CYCLES = ["2026 Graduates", "2026 Graduates"]


def test_inferred_cycle_is_not_recorded():
    # A date-inferred (guessed) cycle must never become a radar "observation" —
    # it would surface as a 🎯 verified drop date and project fiction forward.
    store = {
        "1": {
            "company": "GuessCo",
            "season": "2026 Graduates",
            "season_inferred": True,
            "posted_at": "2026-06-01T00:00:00Z",
        },
        "2": {
            "company": "RealCo",
            "season": "2026 Graduates",
            "season_inferred": False,
            "posted_at": "2026-06-02T00:00:00Z",
        },
    }
    out = observe.update_from_store(store, {"companies": {}}, CYCLES)
    assert "guessco" not in out["companies"]
    assert out["companies"]["realco"]["cycles"]["2026 Graduates"]["first_posted"] == "2026-06-02"


def test_off_tracked_cycle_is_not_recorded():
    # An off-cycle tombstone ("Summer 2026") is real but was never swept in full;
    # recording it would let the radar invent a cadence via prev-cycle projection.
    store = {
        "1": {
            "company": "OneOff",
            "season": "Summer 2026",
            "season_inferred": False,
            "posted_at": "2026-06-18T00:00:00Z",
        },
        "2": {
            "company": "Tracked",
            "season": "2026 Graduates",
            "season_inferred": False,
            "posted_at": "2026-06-18T00:00:00Z",
        },
    }
    out = observe.update_from_store(store, {"companies": {}}, CYCLES)
    assert "oneoff" not in out["companies"]
    assert "tracked" in out["companies"]
