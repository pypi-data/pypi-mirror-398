# footballmvp Analyzer

This project calculates the Most Valuable Player (MVP) for professional football leagues and tournaments using player performance statistics.

Think of it as a custom analytics engine that scrapes, cleans, processes, and visualizes football player data to answer:

"Who’s really been the MVP this season?

Github (FootballMVP): /*https://github.com/DrueStaples08/FootballMVP*/

Github (FootballMVPSampleOutputs): /*https://github.com/DrueStaples08/FootballMVPSampleOutputs*/

## Getting Started
1. Clone the Project
    - Choose your workflow:

        - Option A: Clone (For contributors)
            ```python 
            git clone https://github.com/DrueStaples08/FootballMVP
            ```


        - Option B: Fork (For contributors)
            - Fork the repo on GitHub, then clone your fork:
                ```python 
                git clone https://github.com/DrueStaples08/FootballMVP
                ```


        - Option C: Install via pip (For developers)
            ```python 
            pip install FootballMVP
            ```
            ```python 
            pip install -r requirements.txt
            ```
            ```python 
            python mvp_comp_dir/mvp_run.py
            ```


2. Setup Your Environment
    - Python Version: 3.12 (Required)

    - Install dependencies:
    ```python 
    pip install -r requirements.txt
    ```

    - Using pyenv (recommended):
        ```python 
        pyenv install 3.12.4
        ```
        ```python 
        pyenv virtualenv 3.12.4 soccer-mvp-env
        ```
        ```python 
        pyenv activate soccer-mvp-env
        ```
        ```python 
        pip install -r requirements.txt
        ```

    - Troubleshooting:
        - If you see ModuleNotFoundError: No module named 'distutils', run:
            ```python
            pip install setuptools
            ```


3. Install Java (Needed for PySpark)
    - Install Java 17:
        - brew install openjdk@17
    - Verify Java version:
        - java --version
    - Link Java with Homebrew:
        - sudo ln -sfn /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk /Library/Java/JavaVirtualMachines/openjdk-17.jdk
    - Add this below your shell config (.zshrc or .bashrc):

        export PYENV_ROOT="$HOME/.pyenv"

        export PATH="$PYENV_ROOT/bin:$PATH"

        eval "$(pyenv init --path)"

        eval "$(pyenv init -)"

        eval "$(pyenv virtualenv-init -)"

        export JAVA_HOME="/opt/homebrew/opt/openjdk@17"

        export PATH="$JAVA_HOME/bin:$PATH"

    - Reload your shell:

        ```python 
        source ~/.zshrc
        ```


---

## Input Parameters (Function Call)

```python
def compute_mvp(
    competition_name: str,             # Required
    competition_year: str,             # Required
    scalar: int = 4,                   # Optional
    open_close_league: str = "",       # Optional
    overide: bool = True,              # Optional
    title: str = "",                   # Optional
    percentile_threshold: float = .98, # Optional
    manual_competition_id: str = ""    # Optional
) -> str:
```


---

## Common Workflows & Examples

- All examples assume:

    ```python 
    from FootballMVP import AllCompetitions, Competition, Match, Player, MVP, workflow_compute_mvp
    ```

- Bootstrap: list competitions and add a watchlist entry
    all_comps = AllCompetitions()
    all_comp_info = all_comps.gather_all_competition_ids("https://www.fotmob.com/leagues")  # run
    print(all_comp_info)  # dict: {id: normalized_name}

- Add by normalized name (if present)
    print(all_comps.add_competition_to_my_watchlist(
        competition_name="open-cup",
        gather_all_competition_ids=all_comp_info
    ))

- Or add by explicit URL (if not present or to disambiguate)
    print(all_comps.add_competition_to_my_watchlist(
        competition_name="",
        gather_all_competition_ids=all_comp_info,
        defined_url="https://www.fotmob.com/leagues/47/matches/premier-league"
    ))

- Minimal end-to-end run (MVP workflow)
    print(workflow_compute_mvp(competition_name="mls", competition_year="2025"))

- Custom scalar / title / percentile
    mvp = MVP()
    print(mvp.compute_mvp(
        competition_name="serie",
        competition_year="2024-2025",
        percentile_threshold=.97,
        title="Top 3% MVPs for Serie in 2024-2025"
    ))

- Split seasons (Apertura/Clausura)
    print(workflow_compute_mvp(
        competition_name="liga-mx",
        competition_year="2024-2025",
        open_close_league="Apertura"
    ))
    print(workflow_compute_mvp(
        competition_name="liga-mx",
        competition_year="2024-2025",
        open_close_league="Clausura"
    ))

- Resume runs (no override)
    print(workflow_compute_mvp(
        competition_name="canadian-championship",
        competition_year="2025",
        overide=False
    ))

- Manual competition id (disambiguate leagues)
    - Premier League (England)
        print(workflow_compute_mvp(
            competition_name="premier-league",
            competition_year="2016-2017",
            manual_competition_id="47"
        ))

    - Premier League (Canada)
        print(workflow_compute_mvp(
            competition_name="premier-league",
            competition_year="2019",
            manual_competition_id="9986"
        ))

## Sample Code

### Setup
- `all_comps = AllCompetitions()`
- `all_comp_info = all_comps.gather_all_competition_ids("https://www.fotmob.com/")`
- `print(all_comp_info)`

---

## Add Competitions to Watchlist

### International — Countries
- `print(all_comps.add_competition_to_my_watchlist(competition_name="world-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/77/matches/world-cup"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="euro", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/50/matches/euro"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="copa-america", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/44/matches/copa-america"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="summer-olympics", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/66/matches/summer-olympics"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="concacaf-gold-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/298/matches/concacaf-gold-cup"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="concacaf-nations-league", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/9821/matches/concacaf-nations-league"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="uefa-nations-league-a", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/9806/matches/uefa-nations-league"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="uefa-nations-league-b", gather_all_competition_ids=all_comp_info))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="uefa-nations-league-c", gather_all_competition_ids=all_comp_info))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="uefa-nations-league-d", gather_all_competition_ids=all_comp_info))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="euro-qualification", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/10607/matches/euro-qualification"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="world-cup-qualification-afc", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/10197/matches/world-cup-qualification-afc"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="world-cup-qualification-caf", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/10196/matches/world-cup-qualification-caf"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="world-cup-qualification-concacaf", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/10198/matches/world-cup-qualification-concacaf"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="world-cup-qualification-conmebol", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/10199/matches/world-cup-qualification-conmebol"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="uefa-nations-league-qualification", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/10717/matches/uefa-nations-league-qualification"))`

### International — Clubs
- `print(all_comps.add_competition_to_my_watchlist(competition_name="fifa-intercontinental-cup", gather_all_competition_ids=all_comp_info))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="fifa-club-world-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/78/matches/fifa-club-world-cup"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="champions-league", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/42/matches/champions-league"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="europa-league", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/73/matches/europa-league"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="conference-league", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/10216/matches/conference-league"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="afc-champions-league-elite", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/525/matches/afc-champions-league-elite"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="concacaf-champions-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/297/matches/concacaf-champions-cup"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="copa-sudamericana", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/299/matches/copa-sudamericana"))`

### Countries

#### Austria
- `print(all_comps.add_competition_to_my_watchlist(competition_name="bundesliga", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/38/matches/bundesliga"))`

#### Canada
- `print(all_comps.add_competition_to_my_watchlist(competition_name="canadian-championship", gather_all_competition_ids=all_comp_info))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="premier-league", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/9986/matches/premier-league"))`

#### England
- `print(all_comps.add_competition_to_my_watchlist(competition_name="", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/47/matches/premier-league"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="fa-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/132/matches/fa-cup"))`

#### France
- `print(all_comps.add_competition_to_my_watchlist(competition_name="ligue-1", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/53/matches/ligue-1"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="coupe-de-france", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/134/matches/coupe-de-france"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="trophee-des-champions", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/207/matches/trophee-des-champions"))`

#### Germany
- `print(all_comps.add_competition_to_my_watchlist(competition_name="bundesliga", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/54/matches/bundesliga"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="dfb-pokal", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/209/matches/dfb-pokal"))`

#### Italy
- `print(all_comps.add_competition_to_my_watchlist(competition_name="serie", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/55/matches/serie"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="coppa-italia", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/141/matches/coppa-italia"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="super-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/222/matches/super-cup"))`

#### Mexico
- `print(all_comps.add_competition_to_my_watchlist(competition_name="liga-mx", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/230/matches/liga-mx"))`

#### Netherlands
- `print(all_comps.add_competition_to_my_watchlist(competition_name="eredivisie", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/57/matches/eredivisie"))`

#### Saudi Arabia
- `print(all_comps.add_competition_to_my_watchlist(competition_name="saudi-pro-league", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/536/matches/saudi-pro-league"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="kings-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/9942/matches/kings-cup"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="super-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/10074/matches/super-cup"))`

#### Scotland
- `print(all_comps.add_competition_to_my_watchlist(competition_name="premiership", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/64/matches/premiership"))`

#### Spain
- `print(all_comps.add_competition_to_my_watchlist(competition_name="laliga", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/87/matches/laliga"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="copa-del-rey", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/138/matches/copa-del-rey"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="super-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/139/matches/super-cup"))`

#### USA
- `print(all_comps.add_competition_to_my_watchlist(competition_name="mls", gather_all_competition_ids=all_comp_info))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="open-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/9441/matches/open-cup"))`
- `print(all_comps.add_competition_to_my_watchlist(competition_name="leagues-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/10043/matches/leagues-cup"))`

---

## Run MVP Program

### International — Countries
- `print(workflow_compute_mvp(competition_name="world-cup", competition_year="2014", manual_competition_id="77", scalar=14))`
- `print(workflow_compute_mvp(competition_name="world-cup", competition_year="2018", manual_competition_id="77", scalar=14))`
- `print(workflow_compute_mvp(competition_name="world-cup", competition_year="2022", manual_competition_id="77", scalar=14))`
- `print(workflow_compute_mvp(competition_name="euro", competition_year="2016", scalar=14))`
- `print(workflow_compute_mvp(competition_name="euro", competition_year="2020", scalar=14))`
- `print(workflow_compute_mvp(competition_name="euro", competition_year="2024", scalar=14))`
- `print(workflow_compute_mvp(competition_name="copa-america", competition_year="2016"))`
- `print(workflow_compute_mvp(competition_name="copa-america", competition_year="2019"))`
- `print(workflow_compute_mvp(competition_name="copa-america", competition_year="2021"))`
- `print(workflow_compute_mvp(competition_name="copa-america", competition_year="2024"))`
- `print(workflow_compute_mvp(competition_name="concacaf-gold-cup", competition_year="2025", scalar=14))`
- `print(workflow_compute_mvp(competition_name="concacaf-nations-league", competition_year="2022-2023", scalar=14))`
- `print(workflow_compute_mvp(competition_name="concacaf-nations-league", competition_year="2023-2024", scalar=14))`
- `print(workflow_compute_mvp(competition_name="concacaf-nations-league", competition_year="2024-2025", scalar=14))`

### International — Clubs
- `print(workflow_compute_mvp(competition_name="fifa-intercontinental-cup", competition_year="2024", scalar=14, overide=False, min_req_matches=False))`
- `print(workflow_compute_mvp(competition_name="fifa-club-world-cup", competition_year="2020", scalar=14))`
- `print(workflow_compute_mvp(competition_name="fifa-club-world-cup", competition_year="2021", scalar=14))`
- `print(workflow_compute_mvp(competition_name="fifa-club-world-cup", competition_year="2022", scalar=14))`
- `print(workflow_compute_mvp(competition_name="fifa-club-world-cup", competition_year="2023", scalar=14))`
- `print(workflow_compute_mvp(competition_name="fifa-club-world-cup", competition_year="2025", scalar=14))`
- `print(workflow_compute_mvp(competition_name="champions-league", competition_year="2016-2017", scalar=14))`
- `print(workflow_compute_mvp(competition_name="champions-league", competition_year="2017-2018", scalar=14))`
- `print(workflow_compute_mvp(competition_name="champions-league", competition_year="2018-2019", scalar=14))`
- `print(workflow_compute_mvp(competition_name="champions-league", competition_year="2019-2020", scalar=14))`
- `print(workflow_compute_mvp(competition_name="champions-league", competition_year="2020-2021", scalar=14))`
- `print(workflow_compute_mvp(competition_name="champions-league", competition_year="2021-2022", scalar=14))`
- `print(workflow_compute_mvp(competition_name="champions-league", competition_year="2022-2023", scalar=14))`
- `print(workflow_compute_mvp(competition_name="champions-league", competition_year="2023-2024", scalar=14))`
- `print(workflow_compute_mvp(competition_name="champions-league", competition_year="2024-2025", scalar=14))`
- `print(workflow_compute_mvp(competition_name="europa-league", competition_year="2016-2017", scalar=14))`
- `print(workflow_compute_mvp(competition_name="europa-league", competition_year="2017-2018", scalar=14))`
- `print(workflow_compute_mvp(competition_name="europa-league", competition_year="2018-2019", scalar=14))`
- `print(workflow_compute_mvp(competition_name="europa-league", competition_year="2019-2020", scalar=14))`
- `print(workflow_compute_mvp(competition_name="europa-league", competition_year="2020-2021", scalar=14))`
- `print(workflow_compute_mvp(competition_name="europa-league", competition_year="2021-2022", scalar=14))`
- `print(workflow_compute_mvp(competition_name="europa-league", competition_year="2022-2023", scalar=14))`
- `print(workflow_compute_mvp(competition_name="europa-league", competition_year="2023-2024", scalar=14))`
- `print(workflow_compute_mvp(competition_name="europa-league", competition_year="2024-2025", scalar=14))`
- `print(workflow_compute_mvp(competition_name="afc-champions-league-elite", competition_year="2020", scalar=14))`
- `print(workflow_compute_mvp(competition_name="afc-champions-league-elite", competition_year="2021", scalar=14))`
- `print(workflow_compute_mvp(competition_name="afc-champions-league-elite", competition_year="2022", scalar=14))`
- `print(workflow_compute_mvp(competition_name="afc-champions-league-elite", competition_year="2023-2024", scalar=14))`
- `print(workflow_compute_mvp(competition_name="afc-champions-league-elite", competition_year="2024-2025", scalar=14))`
- `print(workflow_compute_mvp(competition_name="concacaf-champions-cup", competition_year="2020", scalar=14))`
- `print(workflow_compute_mvp(competition_name="concacaf-champions-cup", competition_year="2021", scalar=14))`
- `print(workflow_compute_mvp(competition_name="concacaf-champions-cup", competition_year="2022", scalar=14))`
- `print(workflow_compute_mvp(competition_name="concacaf-champions-cup", competition_year="2023", scalar=14))`
- `print(workflow_compute_mvp(competition_name="concacaf-champions-cup", competition_year="2024", scalar=14))`
- `print(workflow_compute_mvp(competition_name="concacaf-champions-cup", competition_year="2025", scalar=14))`
- `print(workflow_compute_mvp(competition_name="copa-sudamericana", competition_year="2020", scalar=14))`
- `print(workflow_compute_mvp(competition_name="copa-sudamericana", competition_year="2021", scalar=14))`
- `print(workflow_compute_mvp(competition_name="copa-sudamericana", competition_year="2022", scalar=14))`
- `print(workflow_compute_mvp(competition_name="copa-sudamericana", competition_year="2023", scalar=14))`
- `print(workflow_compute_mvp(competition_name="copa-sudamericana", competition_year="2024", scalar=14))`
- `print(workflow_compute_mvp(competition_name="copa-sudamericana", competition_year="2025", scalar=14))`

### USA
- `print(workflow_compute_mvp(competition_name="mls", competition_year="2016", scalar=4))`
- `print(workflow_compute_mvp(competition_name="mls", competition_year="2017", scalar=4))`
- `print(workflow_compute_mvp(competition_name="mls", competition_year="2018", scalar=4))`
- `print(workflow_compute_mvp(competition_name="mls", competition_year="2019", scalar=4))`
- `print(workflow_compute_mvp(competition_name="mls", competition_year="2020", scalar=4))`
- `print(workflow_compute_mvp(competition_name="mls", competition_year="2021", scalar=4))`
- `print(workflow_compute_mvp(competition_name="mls", competition_year="2022", scalar=4))`
- `print(workflow_compute_mvp(competition_name="mls", competition_year="2023", scalar=4))`
- `print(workflow_compute_mvp(competition_name="mls", competition_year="2024", scalar=4))`
- `print(workflow_compute_mvp(competition_name="mls", competition_year="2025", scalar=4))`
- `print(workflow_compute_mvp(competition_name="leagues-cup", competition_year="2023", scalar=14))`
- `print(workflow_compute_mvp(competition_name="leagues-cup", competition_year="2024", scalar=14))`
- `print(workflow_compute_mvp(competition_name="leagues-cup", competition_year="2025", scalar=14))`

### Mexico — Liga MX (split seasons)
- `print(workflow_compute_mvp(competition_name="liga-mx", competition_year="2020-2021", open_close_league="Apertura"))`
- `print(workflow_compute_mvp(competition_name="liga-mx", competition_year="2020-2021", open_close_league="Clausura"))`
- `print(workflow_compute_mvp(competition_name="liga-mx", competition_year="2021-2022", open_close_league="Apertura"))`
- `print(workflow_compute_mvp(competition_name="liga-mx", competition_year="2021-2022", open_close_league="Clausura"))`
- `print(workflow_compute_mvp(competition_name="liga-mx", competition_year="2022-2023", open_close_league="Apertura"))`
- `print(workflow_compute_mvp(competition_name="liga-mx", competition_year="2022-2023", open_close_league="Clausura"))`
- `print(workflow_compute_mvp(competition_name="liga-mx", competition_year="2023-2024", open_close_league="Apertura"))`
- `print(workflow_compute_mvp(competition_name="liga-mx", competition_year="2023-2024", open_close_league="Clausura"))`
- `print(workflow_compute_mvp(competition_name="liga-mx", competition_year="2024-2025", open_close_league="Apertura"))`
- `print(workflow_compute_mvp(competition_name="liga-mx", competition_year="2024-2025", open_close_league="Clausura"))`

### Scotland — Premiership
- `print(workflow_compute_mvp(competition_name="premiership", competition_year="2020-2021", manual_competition_id="64"))`
- `print(workflow_compute_mvp(competition_name="premiership", competition_year="2021-2022", manual_competition_id="64"))`
- `print(workflow_compute_mvp(competition_name="premiership", competition_year="2022-2023", manual_competition_id="64"))`
- `print(workflow_compute_mvp(competition_name="premiership", competition_year="2023-2024", manual_competition_id="64"))`
- `print(workflow_compute_mvp(competition_name="premiership", competition_year="2024-2025", manual_competition_id="64"))`

### Spain — Super Cup & Copa del Rey
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2019-2020", scalar=14, manual_competition_id="139"))`
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2020-2021", scalar=14, manual_competition_id="139"))`
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2021-2022", scalar=14, manual_competition_id="139"))`
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2022-2023", scalar=14, manual_competition_id="139"))`
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2023-2024", scalar=14, manual_competition_id="139"))`
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2024-2025", scalar=14, manual_competition_id="139"))`
- `print(workflow_compute_mvp(competition_name="copa-del-rey", competition_year="2021-2022", scalar=14))`
- `print(workflow_compute_mvp(competition_name="copa-del-rey", competition_year="2022-2023", scalar=14))`
- `print(workflow_compute_mvp(competition_name="copa-del-rey", competition_year="2023-2024", scalar=14))`
- `print(workflow_compute_mvp(competition_name="copa-del-rey", competition_year="2024-2025", scalar=14))`

### Italy — Super Cup & Coppa Italia
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2019-2020", scalar=14, manual_competition_id="222"))`
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2020-2021", scalar=14, manual_competition_id="222"))`
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2021-2022", scalar=14, manual_competition_id="222"))`
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2022-2023", scalar=14, manual_competition_id="222"))`
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2023-2024", scalar=14, manual_competition_id="222"))`
- `print(workflow_compute_mvp(competition_name="super-cup", competition_year="2024-2025", scalar=14, manual_competition_id="222"))`
- `print(workflow_compute_mvp(competition_name="coppa-italia", competition_year="2020-2021", scalar=14))`
- `print(workflow_compute_mvp(competition_name="coppa-italia", competition_year="2021-2022", scalar=14))`
- `print(workflow_compute_mvp(competition_name="coppa-italia", competition_year="2022-2023", scalar=14))`
- `print(workflow_compute_mvp(competition_name="coppa-italia", competition_year="2023-2024", scalar=14))`
- `print(workflow_compute_mvp(competition_name="coppa-italia", competition_year="2024-2025", scalar=14))`

        
    - Step-by-Step
        - List all available competitions (Note: if a competition is not available, include a defined_url arguement)
            - all_comps = AllCompetitions()
            - all_comp_info = all_comps.gather_all_competition_ids("https://www.fotmob.com/") # run
            - print(all_comp_info)

        - Chooses the competition 
            - comps = Competition()
            - print(comps.choose_competition(competition_name="mls", competition_year="2023"))

        - Test this out later to extract player info from new html setup 
            - match = Match()
            - print(match.extract_single_match_players_stats("https://www.fotmob.com/matches/toronto-fc-vs-fc-cincinnati/3vaemjyi#4085040"))
            - print(match.choose_match(competition_name="mls", competition_year="2023"))

        - Extract player stats and compute both the total of games played and average SPI score for only games with SPI scores included. 
            - player = Player()
            - print(player.choose_player_stats(competition_name="mls", competition_year="2023"))
            - print(player.competition_analysis(competition_name="mls", competition_year="2023"))

        - Runs all the steps above
            - mvp = MVP()
            - print(mvp.compute_mvp(competition_name="mls", competition_year="2023", scalar=4))




## Example Output

![](mls_2023_mvp_results_image.png)



## How a Player Receives an SPI Score:

Only players who receive an SPI score are considered to have officially played in a match. 
While the exact time required for a score isn't fully confirmed, starting players typically 
need to play just a few minutes to earn an SPI for that match. On the other hand, substitutes 
must play for approximately 10 minutes to qualify for a score.

Substitute players who play less than the required time or those who are injured shortly after 
entering the game will not receive an SPI score. Initially, I considered assigning a default 
starting score (likely around 6.0 or 7.0, which is what I think a player starts off anyways) to any competitor who participated in the match but didn’t earn 
a score. However, this approach raised concerns: for instance, a player who scores a goal and 
one who concedes an own-goal would both receive the same starting score, which seems inappropriate.

To maintain consistency, this MVP program will only consider a match as "played" if a player has been assigned an SPI rating. 

The FotMob player rating is calculated based on more than 100 individual stats per player per match

---

All Competition names and ids (i.e. all_comp_info):

{'38': 'bundesliga', '40': 'first-division-a', '42': 'champions-league', '43': 'confederation-cup', '44': 'copa-america', '45': 'copa-libertadores', '46': 'superligaen', '48': 'championship', '50': 'euro', '51': 'veikkausliiga', '57': 'eredivisie', '58': 'eredivisie', '64': 'premiership', '65': 'summer-olympics-women', '66': 'summer-olympics', '68': 'allsvenskan', '69': 'super-league', '73': 'europa-league', '85': '1-division', '86': 'serie-b', '108': 'league-one', '109': 'league-two', '112': 'liga-profesional', '113': 'a-league', '114': 'friendlies', '116': 'cymru-premier', '117': 'national-league', '119': '2-liga', '120': 'super-league', '121': 'primera-division', '122': '1-liga', '123': 'championship', '124': 'league-one', '125': 'league-two', '127': 'ligat-haal', '128': 'leumit-league', '129': 'premiership', '130': 'mls', '131': 'liga-1', '132': 'fa-cup', '135': 'super-league-1', '136': '1-division', '137': 'scottish-cup', '140': 'laliga2', '141': 'coppa-italia', '142': 'efl-trophy', '143': 'suomen-cup', '144': 'primera-division', '145': 'greece-cup', '147': 'serie-c', '150': 'coupe-de-la-ligue', '151': 'turkish-cup', '161': 'primera-division', '163': 'challenge-league', '169': 'ettan', '171': 'svenska-cupen', '176': '1-liga', '179': 'challenge-cup', '180': 'league-cup', '181': 'premiership-playoff', '182': 'super-liga', '187': 'league-cup', '189': 'liga-i', '190': 'cupa-româniei', '193': 'russian-cup', '196': 'ekstraklasa', '199': 'division-profesional', '204': 'postnord-ligaen', '205': 'norsk-tipping-ligaen', '207': 'trophée-des-champions', '209': 'dfb-pokal', '215': 'besta-deildin', '217': 'icelandic-cup', '218': 'first-division', '224': 'j-league-cup', '225': 'premier-league', '230': 'liga-mx', '231': 'national-division', '239': '2-division', '240': '3-division', '241': 'danmarksserien', '246': 'serie-a', '251': 'ykkosliiga', '256': 'kvindeligaen', '263': 'premier-league', '264': 'first-division-b', '267': 'premier-league', '270': 'first-professional-league', '273': 'primera-division', '274': 'categoría-primera-a', '287': 'euro-u19', '288': 'euro-u21', '290': 'asian-cup', '292': "women's-euro", '293': "women's-friendlies", '297': 'concacaf-champions-cup', '298': 'concacaf-gold-cup', '299': 'copa-sudamericana', '300': 'east-asian-championship', '301': 'european-championship-u-17', '305': 'toulon-tournament', '329': 'gulf-cup', '331': 'toppserien', '332': '1-division-kvinner', '335': 'primera-division', '336': 'liga-nacional', '337': 'liga-nacional', '338': '1-division', '339': 'primera-division', '342': 'finland-cup', '441': 'premier-league', '489': 'club-friendlies', '512': 'regionalliga', '519': 'premier-league', '524': 'stars-league', '525': 'afc-champions-league-elite', '526': 'caf-champions-league', '529': 'premier-league', '533': 'professional-football-league', '537': 'premier-soccer-league', '544': 'ligue-i', '8815': 'super-league-2', '8870': 'championship', '8944': 'national-north-&-south', '8947': 'premier-division', '8965': 'primera-b-nacional', '8968': 'primera-federación', '8969': 'ykkonen', '8971': 'serie-c', '8973': '2-liga', '8974': 'j-league-2', '8976': 'liga-de-expansión-mx', '8980': 'brazil-state-championship', '9015': 'liga-primera', '9039': 'lpf', '9080': 'k-league-1', '9081': 'bundesliga', '9100': '2-division', '9112': 'liga-3', '9113': 'liga-ii', '9116': 'k-league-2', '9122': 'segunda-division', '9123': 'second-league', '9125': 'primera-b', '9126': 'primera-b', '9134': 'nwsl', '9137': 'china-league-one', '9138': 'segunda-federación', '9141': 'germany-5', '9143': 'singapore-cup', '9210': 'france-4', '9213': 'primera-b-metropolitana-&-torneo-federal-a', '9253': 'fa-trophy', '9265': 'asean-championship', '9294': "women's-championship", '9296': 'usl-league-one', '9305': 'copa-argentina', '9306': 'cecafa-cup', '9345': 'copa-mx', '9375': "women's-champions-league", '9382': 'toppserien-qualification', '9390': 'west-asian-championship', '9391': 'copa-mx-clausura', '9408': 'international-champions-cup', '9422': 'k-league', '9428': 'african-nations-championship', '9429': 'copa-do-nordeste', '9441': 'open-cup', '9468': 'caf-confed-cup', '9469': 'afc-champions-league-two', '9470': 'afc-challenge-league', '9474': 'mtn8', '9478': 'indian-super-league', '9494': 'usl-league-two', '9495': 'a-league-women', '9500': 'we-league-women', '9514': 'the-atlantic-cup', '9537': 'k-league-3', '9545': 'highland-/-lowland', '9579': 'algarve-cup-qualification', '9656': 'concacaf-championship-u20', '9682': 'concacaf-central-american-cup', '9690': 'southeast-asian-games', '9717': "women's-league-cup", '9741': 'uefa-youth-league', '9754': 'obos-ligaen', '9806': 'uefa-nations-league-a', '9807': 'uefa-nations-league-b', '9808': 'uefa-nations-league-c', '9809': 'uefa-nations-league-d', '9821': 'concacaf-nations-league', '9833': 'asian-games', '9837': 'canadian-championship', '9841': 'afc-u20-asian-cup', '9876': 'saff-championship', '9906': 'liga-mx-femenil', '9907': 'liga-f', '9921': 'shebelieves-cup-qualification', '9986': 'premier-league', '10007': 'copa-de-la-liga-profesional', '10022': 'regionalliga', '10043': 'leagues-cup', '10046': 'copa-ecuador', '10056': 'liga-2', '10075': 'torneo-de-verano', '10076': 'league-cup', '10082': 'fa-cup-women', '10084': 'nisa', '10145': 'footballs-staying-home-cup-(esports)', '10167': 'nwsl-challenge-cup', '10176': 'premier-league-2-div-2', '10178': 'serie-a-femminile', '10188': 'k-league-3', '10207': 'nisa-legends-cup', '10216': 'conference-league', '10242': 'fifa-arab-cup', '10244': 'paulista-a1', '10269': 'womens-asian-cup', '10270': 'league-cup', '10272': 'carioca', '10273': 'mineiro', '10274': 'gaúcho', '10290': 'baiano', '10291': 'goiano', '10304': 'finalissima', '10309': 'durand-cup', '10310': 'stars-league-relegation-playoff', '10325': 'preseason', '10366': 'super-cup', '10368': 'copa-america-femenina', '10437': 'euro-u-21', '10449': 'nacional-feminino', '10457': "uefa-women's-nations-league-a", '10458': 'uefa-nations-league-b-women', '10459': 'uefa-nations-league-c-women', '10474': 'arab-club-champions-cup', '10498': 'summer-olympics-concacaf-qualification', '10508': 'african-football-league', '10511': 'afc-summer-olympics-women', '10584': 'south-africa-league', '10603': 'concacaf-gold-cup-women', '10607': 'euro', '10609': 'asian-cup--playoff', '10610': 'concafaf-gold-cup', '10611': 'champions-league', '10612': "women's-champions-league", '10613': 'europa-league', '10615': 'conference-league', '10616': 'euro-u19', '10617': 'euro-u17', '10618': 'copa-libertadores', '10619': 'caf-champions-league', '10621': 'concacaf-championship-u20', '10622': 'afc-champions-league-elite', '10623': 'copa-sudamericana', '10640': "women's-euro-league-a", '10641': "women's-euro-league-b", '10642': "women's-euro-league-c", '10649': 'nwsl-x-liga-mx', '10651': 'copa-de-la-reina', '10654': 'usl-jägermeister-cup', '10699': 'usl-super-league-women', '10703': 'fifa-intercontinental-cup', '10705': 'national-league-cup', '10708': 'knockout-cup', '10717': 'uefa-nations-league-a', '10718': 'uefa-nations-league-b', '10719': 'uefa-nations-league-c', '10791': 'swpl-1', '10840': 'baller-league', '10844': 'baller-league', '10872': 'northern-super-league'}

---

Resource: 
- (Fotmob Homepage) - */https://www.fotmob.com/*

- (Install Pyspark) - */https://medium.com/@jpurrutia95/install-and-set-up-pyspark-in-5-minutes-m1-mac-eb415fe623f3/*

---

### Potential Contributions:
- Add an option for storing results in a Cloud data storage 

### Possibilites to optimize the MVP algorithm
- Add more weighted features:
    - players
        - avg spi for all (or specific) competitions
        - avg spi from past N years/months/weeks/games 
    - teams
    - leagues or tournaments
    - countries
    - continents 
    - match type 
        - e.g. 
            - "finalTournament":"Final","bronzeFinal":"Bronze-final","semifinal":"Semi-final","quarterfinal":"Quarter-final","roundof16":"Round of 16","h2h":"Head-to-Head","bracket":"Bracket"

---

Made by Drue Tomas Staples

