import re
import time
import json
import os

import requests
from typing import List, Dict
from bs4 import BeautifulSoup

import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import requests


from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, desc
from pyspark.sql.types import StringType
from pyspark.sql.types import StructType, StringType, FloatType, StructField, IntegerType
from pyspark.sql.functions import round as pyspark_round
from pyspark.errors import AnalysisException

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import logging



from pyspark.sql import SparkSession, functions as F
from pyspark.sql.window import Window
from pyspark.sql.functions import desc

import json
import re
import time
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup



logging.basicConfig(level=logging.INFO)


class AllCompetitions:
    """Scrape FotMob competitions and manage a local competition watchlist.


    This class fetches competition metadata from FotMob, normalizes league
    names, and appends selected competitions to a local Spark-backed CSV
    watchlist stored under the `all_comps_df/` directory.


    Attributes:
    fotmob_leagues_url (str): Base URL for FotMob leagues.
    last_competitiion_index (int): Upper bound index used by the author for iteration.
    start_competition_index (int): Lower bound index used by the author for iteration.


    Examples:
    >>> all_comps = AllCompetitions()
    >>> all_ids = all_comps.gather_all_competition_ids(all_comps.fotmob_leagues_url)
    >>> all_comps.add_competition_to_my_watchlist("mls", all_ids)
    "New Competition Added: mls" # or a duplicate/created message
    """  
    def __init__(self):
        """Initialize defaults for FotMob league scraping and indexing.


        Examples:
        >>> AllCompetitions() # basic construction
        Fotmob Leagues URL: https://www.fotmob.com/leagues, Starting Index for Competitions 38, Ending Index for Competitions 306 # doctest: +ELLIPSIS
        """
        self.fotmob_leagues_url = "https://www.fotmob.com/leagues"
        self.last_competitiion_index = 306
        self.start_competition_index = 38



    def __repr__(self):
        """Return a concise summary of key AllCompetitions settings.


        Examples:
        >>> repr(AllCompetitions()) # doctest: +ELLIPSIS
        'Fotmob Leagues URL: https://www.fotmob.com/leagues, Starting Index for Competitions 38, Ending Index for Competitions 306'
        """
        return f"Fotmob Leagues URL: {self.fotmob_leagues_url}, Starting Index for Competitions {self.start_competition_index}, Ending Index for Competitions {self.last_competitiion_index}"



    def gather_all_competition_ids(self, url: str)->Dict:
        """Fetch competition IDs and names from a FotMob leagues page.


        The page contains a JSON blob (`__NEXT_DATA__`) with translation
        mappings. This method extracts the TournamentPrefixes mapping and
        returns a normalized dictionary of `{id: formatted_name}`.


        Print this out to view competition names
        NOTE: Not all competitions will be included in the json output
        Therefore do the following: 
        - Use the defined_url parameter to specify a tournament or league that is not included.
        - And/Or include a manual_competition_id if there are other competitions with the same name e.g. There is a premier-league in both England and Canada



        Args:
        url: URL of the FotMob leagues page (e.g., "https://www.fotmob.com/leagues").


        Returns:
        Dict: Mapping from competition ID (str) to normalized competition name (str).


        Raises:
        requests.exceptions.RequestException: If the HTTP request fails.
        KeyError: If expected keys are missing in the page JSON.
        json.JSONDecodeError: If the embedded JSON cannot be parsed.


        Examples:
        >>> comp = AllCompetitions()
        >>> comp_ids = comp.gather_all_competition_ids(comp.fotmob_leagues_url)
        >>> comp_ids.get("47") # Premier League, for example
        'premier-league' # value depends on site content
        """
        html_doc = requests.get(url)
        html_doc_text = html_doc.text
        soup = BeautifulSoup(html_doc_text, "html.parser")
        scripts = soup.find("script", {"id": "__NEXT_DATA__", "type": "application/json"})
        scripts_str = scripts.string
        scripts_json = json.loads(scripts_str)
        tournament_prefixes_dict = scripts_json["props"]["pageProps"]["fallback"]["/api/translationmapping?locale=en"]["TournamentPrefixes"]
        new_comp_dict = self.format_competition_names(tournament_prefixes_dict)
        """
        Print this out to view competition names
        NOTE: Not all competetitions will be included in this json output
        Therefore do the following: 
        - Use the defined_url parameter to specify a tournament or league that is not included.
        - And/Or include a manual_competition_id if there are other competitions with the same name e.g. There is a premier-league in both England and Canada
        """
        return new_comp_dict



    def format_competition_names(self, tournament_prefixes_dict: Dict)->Dict: 
        """Normalize raw competition names to a kebab-case format.


        Normalization rules:
        - Lowercase
        - Spaces -> hyphens
        - "(w)" -> "qualification"
        - "(women)" -> "women"
        - Remove periods


        Args:
        tournament_prefixes_dict: Raw mapping from competition ID to display name.


        Returns:
        Dict: `{id: normalized_name}` suitable for URLs and folder names.


        Examples:
        >>> AllCompetitions().format_competition_names({"55": "Serie A", "72": "La Liga"})
        {'55': 'serie-a', '72': 'la-liga'}
        """
        new_comp_dict = {i[0]: i[1].lower().replace(" ", "-").replace("(w)", "qualification").replace("(women)", "women").replace(".", "") for i in tournament_prefixes_dict.items()}
        return new_comp_dict
    

    def add_competition_to_my_watchlist(self, competition_name: str, gather_all_competition_ids: Dict, defined_url: str = "") -> str:
        """Append a competition to the local watchlist CSV.


        You can either:
        1) Provide a normalized `competition_name` present in `gather_all_competition_ids`,
        or
        2) Provide a `defined_url` of the form
        "https://www.fotmob.com/leagues/<id>/matches/<name>"


        Creates `all_comps_df/` if it does not exist. Uses Spark to write/append CSV.


        Args:
        competition_name: Normalized competition name (e.g., 'serie-a').
        gather_all_competition_ids: Mapping from ID -> normalized name (output of
        `gather_all_competition_ids`).
        defined_url: Optional explicit FotMob URL containing ID and name.


        Returns:
        str: Human-readable status about creation, addition, or duplicates.

        Examples:
        Add by normalized name:


        >>> all_comps = AllCompetitions()
        >>> ids = all_comps.gather_all_competition_ids(all_comps.fotmob_leagues_url)
        >>> all_comps.add_competition_to_my_watchlist("open-cup", ids)
        'New Competition Added: open-cup' # or duplicate message


        Add by explicit URL:


        >>> all_comps.add_competition_to_my_watchlist(
        ... competition_name="",
        ... gather_all_competition_ids={},
        ... defined_url="https://www.fotmob.com/leagues/77/matches/world-cup",
        ... )
        'Watchlist created and competition ' # first-time create or appended
        """
        if not defined_url:
            all_competition_ids = gather_all_competition_ids.items()
            try:
                single_competition_id = [
                    single_competition[0]
                    for single_competition in all_competition_ids
                    if single_competition[1] == competition_name
                ][0]
            except IndexError as e:
                return f"""
                {e} ---
                To add a competition, you must either:
                - Provide a valid competition_name that exists in the scraped list, OR
                - Provide a defined_url directly.

                Examples:
                1. By name:
                comp.add_competition_to_my_watchlist("serie-a", all_comp_info)

                2. By URL:
                comp.add_competition_to_my_watchlist("", {{}}, defined_url="https://www.fotmob.com/leagues/55/matches/serie-a")
                """
            new_row_data = [
                (
                    f"https://www.fotmob.com/leagues/{single_competition_id}/matches/{competition_name}",
                    str(single_competition_id),
                    competition_name,
                )
            ]
        else:
            match = re.search(r"/leagues/(\d+)/matches/([^/]+)", defined_url)
            if match:
                single_competition_id = match.group(1)
                competition_name = match.group(2)
                new_row_data = [(defined_url, single_competition_id, competition_name)]
            else:
                return "Invalid URL. Example: https://www.fotmob.com/leagues/55/matches/serie-a"

        # Initialize Spark and schema
        spark = SparkSession.builder.getOrCreate()
        schema = StructType() \
            .add("competition_url", StringType(), True) \
            .add("competition_id", StringType(), True) \
            .add("competition_name", StringType(), True)
        
        output_path = "all_comps_df"
        new_row_df = spark.createDataFrame(new_row_data, schema=schema)

        # If directory doesn't exist, create it and write the file
        if not os.path.exists(output_path):
            logging.info("Watchlist not found. Creating new all_comps_df directory.")
            new_row_df.write.mode("overwrite").option("header", "true").csv(output_path)
            return f"Watchlist created and competition '{competition_name}' added."

        # If directory exists, check for duplicates
        existing_df = spark.read.option("header", "true").schema(schema).csv(output_path)
        duplicate_df = existing_df.filter(
            (existing_df.competition_id == str(single_competition_id)) &
            (existing_df.competition_name == competition_name)
        )

        if duplicate_df.count() > 0:
            return f"Competition '{competition_name}' already exists in the watchlist."

        # Append new row
        new_row_df.write.mode("append").option("header", "true").csv(output_path)
        return f"New Competition Added: {competition_name}"







class Competition:
    """Collect match links for a competition and persist them to CSV.

    Finds the competition in the local watchlist, paginates FotMob match listings,
    and writes the consolidated list of `match_url` records for downstream processing.

    Examples:
        Basic (MLS 2025):
        >>> Competition().choose_competition("mls", "2025")
        True

        Apertura/Clausura example (Liga MX):
        >>> Competition().choose_competition("liga-mx", "2023-2024", open_close_league="Apertura")
        True
    """
    def __init__(self):
        """Initialize with empty name/year placeholders.

        Examples:
            >>> c = Competition(); (c.competition_name, c.year)
            (None, None)
        """
        self.competition_name = None
        self.year = None



    def __repr__(self):
        """Return a concise summary of the selected competition.

        Examples:
            >>> c = Competition(); c.competition_name, c.year = "mls", "2025"
            >>> repr(c)
            'Competition Name: mls, Year: 2025'
        """
        return f"Competition Name: {self.competition_name}, Year: {self.year}" 



    def choose_competition(self, competition_name: str,competition_year: str, open_close_league:str="", manual_competition_id:str="")->bool:
        """Resolve a competition from the watchlist and persist its match links.

        Reads `all_comps_df/`, finds the `competition_id` (optionally with manual override
        or Apertura/Clausura), scrapes match URLs, and writes `<dir>/<name>_<year>.csv`.

        Args:
            competition_name: Normalized league name (e.g., "premier-league").
            competition_year: Season label (e.g., "2023" or "2020-2021").
            open_close_league: Subseason label (e.g., "Apertura", "Clausura"). Optional.
            manual_competition_id: Explicit FotMob competition ID to disambiguate. Optional.

        Returns:
            bool: True if CSV written successfully, False if the competition was not found.

        Examples:
            Premier League with manual ID:
            >>> Competition().choose_competition("premier-league", "2023", manual_competition_id="47")
            True

            Liga MX Clausura:
            >>> Competition().choose_competition("liga-mx", "2022-2023", open_close_league="Clausura")
            True
        """
        if open_close_league and not manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{open_close_league}_dir"
        elif not open_close_league and manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{manual_competition_id}_dir"
        elif open_close_league and manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{open_close_league}_{manual_competition_id}_dir"
        else:
            comp_dir = f"{competition_name}_{competition_year}_dir"

        spark_sess = SparkSession.builder.appName("SingleCompetitionSession").getOrCreate()
        df = spark_sess.read.csv(path=f"all_comps_df", header=True, inferSchema=True)
        print(df.show(), "\n\n")
        print("*"*40)
        if not manual_competition_id:
            single_competition_collection = df.select(df.competition_name, df.competition_id).filter(df.competition_name == competition_name).collect()
        else:
            single_competition_collection = df.select(df.competition_name, df.competition_id).filter((df.competition_name == competition_name) & (df.competition_id == manual_competition_id)).collect()
        try:
            competition_name = single_competition_collection[0].competition_name
        except IndexError as e:
            return False
        
        competition_id =  single_competition_collection[0].competition_id
        competition = {"competition_name": competition_name, "competition_id": competition_id, "competition_year": competition_year}
        all_match_links = self.contain_all_match_links(competition["competition_id"], competition["competition_name"], competition["competition_year"], open_close_league)
        data = list(zip(all_match_links, [competition_name]*len(all_match_links), [competition_year]*len(all_match_links)))

        temp_df = spark_sess.createDataFrame(data, schema="match_url string, competition_name string, competition_year string") #newly added line
        temp_df.write.mode("overwrite").csv(f"{comp_dir}/{competition_name}_{competition_year}.csv", header=True)

        logging.info(f"Data for {competition['competition_name']} in {competition['competition_year']} Downloaded Successfully!")
        spark_sess.stop()
        return True



    def contain_all_match_links(self, competition_id: int, competition_name: str, competition_year: str, open_close_league:str="") -> List[str]:
        """Collect all unique match URLs for a competition by paging the listing.

        Args:
            competition_id: FotMob competition ID.
            competition_name: Normalized competition name.
            competition_year: Season or year string (e.g., "2023").
            open_close_league: Optional subseason label for split leagues.

        Returns:
            List[str]: De-duplicated list of match URLs.

        Notes:
            Sleeps between page requests to reduce risk of throttling.

        Examples:
            >>> Competition().contain_all_match_links(47, "premier-league", "2023")[:5]  # doctest: +ELLIPSIS
            ['https://www.fotmob.com/matches/...', ...]
        """
        all_links = set() 
        page_number = 0
        competition_id = str(competition_id)

        if not open_close_league:
            url = f"https://www.fotmob.com/leagues/{competition_id}/matches/{competition_name}?season={competition_year}&page={page_number}"
        else:
            # e.g. https://www.fotmob.com/leagues/230/matches/liga-mx?season=2020-2021+-+Apertura&page=14
            url = f"https://www.fotmob.com/leagues/{competition_id}/matches/{competition_name}?season={competition_year}+-+{open_close_league}&group=by-date&page={page_number}"

        logging.info(f"Scraping all pages in case of any rescheduled matches")
        while True:
            time.sleep(5)
            logging.info(f"Scraping page {page_number}")
            links_per_page = self.extract_match_links_per_page(url)

            new_links = set(links_per_page) - all_links

            if not new_links:
                logging.info(f"No new links found on page {page_number}. Ending pagination.")
                break

            all_links.update(new_links)
            page_number += 1

        return list(all_links)



    def extract_match_links_per_page(self, url: str)-> List:
        """Extract match links from a single competition matches page.

        Parses embedded scripts for `/matches/...#<id>` occurrences, builds absolute
        URLs, and de-duplicates links found across script tags.

        Args:
            url: FotMob competition matches page URL (single page).

        Returns:
            List[str]: Unique match URLs discovered on the page.

        Examples:
            >>> Competition().extract_match_links_per_page("https://www.fotmob.com/leagues/44/matches/premier-league?season=2023&page=0")[:3]  
            ['https://www.fotmob.com/matches/...', ...]
        """
        html_doc = requests.get(url)
        html_doc_text = html_doc.text
        soup = BeautifulSoup(html_doc_text, "html.parser")
        scripts = soup.find_all("script")
        base_url = "https://www.fotmob.com"
        pattern = r'"/matches/[^"]+"'
        match_links = []
        match_ids = []
        seen_match_ids = set()  

        for script in scripts:
            time.sleep(5)
            try:
                json_data = script.string
                if json_data:
                    links = re.findall(pattern, json_data)
                    for link in links:
                        cleaned_link = link.replace('"', '')
                        full_url = base_url + cleaned_link
                        parts = cleaned_link.split('/')
                        if parts:
                            match_id_part = parts[-1]  # e.g., 'ao0uywu#3057298'
                            if match_id_part not in seen_match_ids:
                                seen_match_ids.add(match_id_part)
                                match_links.append(full_url)
                                match_ids.append(match_id_part)

            except Exception as e:
                logging.info(f"Error processing script: {e}")

        match_links = list(set(match_links))
        return match_links






    



class Match:
    """Extract and persist per-match player statistics.

    Loads the Stats tab (headless Chrome), parses a fallback HTML table and embedded
    JSON to collect player SPI ratings and metadata, then writes combined results.

    Examples:
        Resume mode (only fill missing stats):
        >>> Match().choose_match("open-cup", "2025", overide=False)
        # writes 'open-cup_2025_match_stats.csv' under the competition dir
    """
    def __init__(self):
        """No-op initializer for Match extraction helper.

        Examples:
            >>> Match()
            Match()
        """
        pass



    def __repr__(self):
        """Return a simple identifier for the Match helper.

        Examples:
            >>> repr(Match())
            'Match()'
        """
        # Change
        return "Match()"
    


    def choose_match(self, competition_name: str, competition_year: str, open_close_league:str="", overide:bool=True, manual_competition_id:str="")->None:
        """Iterate season match URLs and collect player stats.

        Reads `<comp_dir>/<name>_<year>.csv`, iterates `match_url` values, and aggregates
        player statistics into `<name>_<year>_match_stats.csv`. If `overide=False` and a
        stats CSV exists, resumes by only filling rows with empty `player_stats`.

        Args:
            competition_name: Normalized league name.
            competition_year: Season label.
            open_close_league: Optional subseason label.
            overide: If True, recompute all; if False, only fill missing matches.
            manual_competition_id: Optional override to disambiguate directory.

        Returns:
            None

        Examples:
            Recompute everything for MLS 2025:
            >>> Match().choose_match("mls", "2025", overide=True)

            Resume a prior run for World Cup 2018 (ID override in folder name):
            >>> Match().choose_match("world-cup", "2018", manual_competition_id="77", overide=False)
        """
        spark_sess = SparkSession.builder.appName("MatchSession").getOrCreate()

        if open_close_league and not manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{open_close_league}_dir"
        elif not open_close_league and manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{manual_competition_id}_dir"
        elif open_close_league and manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{open_close_league}_{manual_competition_id}_dir"
        else:
            comp_dir = f"{competition_name}_{competition_year}_dir"

        temp_match_df = spark_sess.read.csv(
                path=f"{comp_dir}/{competition_name}_{competition_year}.csv",
                header=True, inferSchema=True
            )
        
        all_player_stats = []


        if not overide:
            try: 
                existing_match_links_csv = spark_sess.read.csv(
                    f"{comp_dir}/{competition_name}_{competition_year}_match_stats.csv",
                    header=True
                )
                
                # Filter rows where player_stats is null or empty, and extract match_url only
                # I.e extract matches that haven't been played yet
                empty_match_links = (
                existing_match_links_csv
                .filter(existing_match_links_csv["player_stats"] == "[]")
                .select(["match_url"])
                .distinct()
                .rdd.flatMap(lambda x: x)
                .collect()
                )
                # Filter rows where player_stats is NOT null or empty, and extract match_url only
                # I.e extract matches that have been played yet
                finished_match_links = (
                existing_match_links_csv
                .filter(existing_match_links_csv["player_stats"] != "[]")
                .select(["match_url", "competition_name", "competition_year", "player_stats"])
                .distinct()
                .rdd.map(lambda row: Row(match_url=row["match_url"], player_stats=row["player_stats"]))
                .collect()
                )

                all_match_links = empty_match_links
                print(f"Process to not overide the computed player stats: {all_match_links}")

            except AnalysisException as e:
                logging.info("Match Stats CSV does not exist yet.")
                all_match_links = []                 
        else:
            all_match_links = [row["match_url"] for row in temp_match_df.select("match_url").collect()]

        if not all_match_links:
            logging.info("No match links found to process. Competition has either finished or hasn't been updated in Fotmob.")
            spark_sess.stop()
            return
        
        match_set = set()
        count = 0
        number_of_matches = len(all_match_links)

        for match_link in all_match_links:
        # Uncomment to extract the stats only from the first 3 matches instead of testing the program over the entire season    
        # for match_link in all_match_links[:3]:

            count += 1
            match_id = str(match_link.split("#")[1])
            if match_id in match_set:
                logging.info(f"Duplicate Match IDs found for {match_link}. Skipping {count}/{number_of_matches} matches.")
                continue

            match_set.add(match_id)
            time.sleep(5)
            logging.info(f"Processing {count}/{number_of_matches} matches: {match_link}")

            # Extract player stats
            player_stats = self.extract_single_match_players_stats(match_link)
            logging.info(f"All player stats: {player_stats}")


            # Append as a Row with match_url and player_stats (as JSON string)
            all_player_stats.append(
                Row(match_url=match_link, player_stats=json.dumps(player_stats))
            )

        if not overide:
            all_player_stats = all_player_stats + finished_match_links

        # Create DataFrame from list of Rows
        player_stats_df = spark_sess.createDataFrame(all_player_stats)

        # Join with match_df using match_url
        combined_df = temp_match_df.join(player_stats_df, on="match_url", how="inner")

        # New - Error adding duplicate data 
        combined_df = combined_df.dropDuplicates(["match_url"])

        # Save to CSV
        combined_df.write.mode("overwrite").csv(
                f"{comp_dir}/{competition_name}_{competition_year}_match_stats.csv",
                header=True
            )

        logging.info("Player Stats have been saved successfully!")
        spark_sess.stop()



    def extract_single_match_players_stats(self, url: str) -> List[Dict]:
        """Scrape the Stats tab for a single match and return player stats.

        Uses headless Chrome to load `:tab=stats`, then parses fallback HTML and embedded
        lineup JSON to assemble player records:
        - Player_ID (str)
        - Player_Name (str)
        - Shirt_Number (str/int-like or 'NA')
        - Country (str or 'NA')
        - Team_Name (str or 'NA')
        - SPI_Score (stringified numeric; '-1.0' when missing)

        Args:
            url: Base match URL (without the ':tab=stats' suffix).

        Returns:
            List[Dict[str, Any]]: Player statistic dictionaries for the match.

        Raises:
            WebDriverException: If Chrome cannot be started or the page fails to load.

        Examples:
            >>> Match().extract_single_match_players_stats("https://www.fotmob.com/matches/toronto-fc-vs-fc-cincinnati/3vaemjyi#4085040") 
            [{'Player_ID': '...', 'Player_Name': '...', ...}, ...]
        """

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1400,900")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        driver = webdriver.Chrome(options=options)
        driver.get(url + ":tab=stats")
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        player_stats: List[Dict] = []

        # Fallback HTML player table
        fallback_rows = soup.find_all("tr", class_=re.compile(r"css-[\w\d]+-TableRowStyled"))

        for row in fallback_rows:
            try:
                name_span = row.find("span", class_=re.compile(r"css-[\w\d]+-PlayerName"))
                if not name_span:
                    continue
                player_name = name_span.text.strip()

                link = row.find("a")["href"]
                player_id_match = re.search(r"player=(\d+)", link)
                if not player_id_match:
                    continue
                player_id = player_id_match.group(1)

                rating_div = row.find("div", class_=re.compile(r"css-[\w\d]+-PlayerRatingCSS"))
                spi_rating = rating_div.text.strip() if rating_div else None

                # Check for minutes played 
                if not spi_rating:
                    # continue
                    spi_rating = "-1.0"

                # Default metadata values
                shirt_number, team_name, country = "NA", "NA", "NA"

                # Extract metadata from embedded JSON
                for tag in soup.find_all("script"):
                    if tag.string and 'lineup' in tag.string:
                        try:
                            match = re.search(r'"lineup":({.*?}),"hasPlayoff"', tag.string)
                            if match:
                                lineup = json.loads(match.group(1))
                                for team_key in ['homeTeam', 'awayTeam']:
                                    team = lineup.get(team_key, {})
                                    team_name = team.get("name", "NA")
                                    for role in ['starters', 'subs']:
                                        for player in team.get(role, []):
                                            if str(player.get("id")) == player_id:
                                                shirt_number = player.get("shirtNumber", "NA")
                                                country = player.get("countryName", "NA")
                                                raise StopIteration
                        except StopIteration:
                            break
                        except Exception as e:
                            logging.warning(f"JSON extraction error: {e}")

                player_stats.append({
                    "Player_ID": player_id,
                    "Player_Name": player_name,
                    "Shirt_Number": shirt_number,
                    "Country": country,
                    "Team_Name": team_name,
                    "SPI_Score": spi_rating
                })

                logging.info(f"{player_name} | {team_name} | {country} | Rating: {spi_rating}")

            except Exception as e:
                logging.warning(f"Error parsing fallback row: {e}")
                continue

        return player_stats





class Player:
    """Transform match-level player stats to per-player aggregates and analysis.

    Two steps:
    1) `choose_player_stats`: flatten and persist raw per-appearance stats.
    2) `competition_analysis`: compute matches played and average SPI per player,
        filling missing categorical fields with modal values.

    Examples:
        >>> p = Player()
        >>> p.choose_player_stats("open-cup", "2025")
        >>> p.competition_analysis("open-cup", "2025")
    """
    def __init__(self):
        """No-op initializer for Player processing.

        Examples:
            >>> Player()
            Player()
        """
        pass


    def __repr__(self):
        """Return a simple identifier for the Player helper.

        Examples:
            >>> repr(Player())
            'Player()'
        """
        # Fix
        return "Player()"


    def choose_player_stats(self, competition_name: str, competition_year: str, open_close_league:str="", manual_competition_id:str="")->None:
        """Persist basic per-appearance player stats extracted from match CSV.

        Reads `<comp_dir>/<name>_<year>_match_stats.csv`, expands the JSON `player_stats`
        column into rows, and writes a flat CSV `<name>_<year>_player_stats.csv` with:
        `player_id`, `player_name`, `player_number` (-1 if NA), `team_name`,
        `country_name`, `spi_score` (-1.0 if NA).

        Args:
            competition_name: Normalized league name.
            competition_year: Season label.
            open_close_league: Optional subseason label.
            manual_competition_id: Optional override to disambiguate directory.

        Returns:
            None

        Examples:
            >>> Player().choose_player_stats("mls", "2025")
        """

        spark_sess = SparkSession.builder.appName("PlayerStatsSession").getOrCreate()

        if open_close_league and not manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{open_close_league}_dir"
        elif not open_close_league and manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{manual_competition_id}_dir"
        elif open_close_league and manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{open_close_league}_{manual_competition_id}_dir"
        else:
            comp_dir = f"{competition_name}_{competition_year}_dir"

        df = spark_sess.read.csv(
                f"{comp_dir}/{competition_name}_{competition_year}_match_stats.csv",
                header=True, inferSchema=True
            )

        match_stats = df.select("player_stats")
        match_rows = match_stats.collect()

        all_player_ids = []
        all_player_names = []
        all_shirt_numbers = []
        all_team_names = []
        all_country_names = []
        all_spi_scores = []

        for row in match_rows:
            # List of player dictionaries
            player_info = json.loads(row.player_stats)  

            for player in player_info:
                player_id = player.get("Player_ID")
                name = player.get("Player_Name")
                number = player.get("Shirt_Number")
                team_name = player.get("Team_Name")
                country = player.get("Country")
                spi = player.get("SPI_Score")

                if player_id and name and number and team_name and country and spi:
                    all_player_ids.append(player_id)
                    all_player_names.append(name)
                    all_shirt_numbers.append(int(number) if number.isdigit() else -1)

                    all_team_names.append(team_name)
                    all_country_names.append(country)

                    try:
                        all_spi_scores.append(float(spi))
                    except ValueError:
                        all_spi_scores.append(-1.0)

                        record["team_name"] = team_name

        logging.info(f"Collected {len(all_player_names)} player stats.")

        data = list(zip(all_player_ids, all_player_names, all_shirt_numbers, all_team_names, all_country_names, all_spi_scores))

        new_schema = StructType([
            StructField("player_id", StringType(), True),
            StructField("player_name", StringType(), True),
            StructField("player_number", IntegerType(), True),
            StructField("team_name", StringType(), True),
            StructField("country_name", StringType(), True),
            StructField("spi_score", FloatType(), True)
        ])

        new_df = spark_sess.createDataFrame(data, schema=new_schema)
        new_df.write.mode("overwrite").csv(
                f"{comp_dir}/{competition_name}_{competition_year}_player_stats.csv",
                header=True
            )   
        print(new_df.show())
        logging.info("All players' basic stats have been saved successfully!")

        spark_sess.stop()





    def competition_analysis(self, competition_name: str, competition_year: str, open_close_league:str="", manual_competition_id:str="")->None:
        """Compute matches played and average SPI per player; fill missing fields.

        Steps:
        - Filter out players where invalid SPI counts (-1.0) exceed valid counts.
        - Compute average SPI excluding -1.0 values.
        - Compute per-player modal values for name, number, team, and country.
        - Write `<name>_<year>_player_stats_analysis.csv` sorted by avg SPI (desc).

        Args:
            competition_name: Normalized league name.
            competition_year: Season label.
            open_close_league: Optional subseason label.
            manual_competition_id: Optional override to disambiguate directory.

        Returns:
            None

        Examples:
            >>> Player().competition_analysis("mls", "2025")
        """
        spark = SparkSession.builder.appName("CompetitionAnalysis").getOrCreate()

        if open_close_league and not manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{open_close_league}_dir"
        elif not open_close_league and manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{manual_competition_id}_dir"
        elif open_close_league and manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{open_close_league}_{manual_competition_id}_dir"
        else:
            comp_dir = f"{competition_name}_{competition_year}_dir"

        df = spark.read.csv(f"{comp_dir}/{competition_name}_{competition_year}_player_stats.csv", header=True, inferSchema=True)

        # Compute matches played per player
        matches_played_per_player = df.groupBy("player_id").count()

        # Count the -1.0 and non -1.0 spi_scores per player
        player_counts = (
            df.groupBy("player_id")
            .agg(
                F.sum(F.when(F.col("spi_score") == -1.0, 1).otherwise(0)).alias("count_invalid"),
                F.sum(F.when(F.col("spi_score") != -1.0, 1).otherwise(0)).alias("count_valid")
            )
        )

        # Filter players: keep only those where valid >= invalid
        filtered_players = player_counts.filter(F.col("count_valid") >= F.col("count_invalid"))

        # Join back to original df so only valid players remain
        df_filtered = df.join(filtered_players.select("player_id"), on="player_id", how="inner")

        # Compute average SPI score per player (ignoring -1.0)
        avg_spi_per_player = (
            df_filtered.filter(F.col("spi_score") != -1.0)
            .groupBy("player_id")
            .agg(F.avg("spi_score").alias("avg_spi_score"))
        )

        # Helper to find the mode (most frequent) value per player for a column
        def mode_column(df, group_col, target_col):
            freq_df = df.groupBy(group_col, target_col).count()
            w = Window.partitionBy(group_col).orderBy(F.desc("count"))
            freq_df = freq_df.withColumn("rank", F.row_number().over(w))
            mode_df = freq_df.filter("rank = 1").select(group_col, F.col(target_col).alias(f"{target_col}_mode"))
            return mode_df

        player_name_mode_df = mode_column(df, "player_id", "player_name")
        player_number_mode_df = mode_column(df, "player_id", "player_number")
        team_name_mode_df = mode_column(df, "player_id", "team_name")
        country_name_mode_df = mode_column(df, "player_id", "country_name")

        # Join matches and avg SPI
        all_player_stats_df = matches_played_per_player.join(avg_spi_per_player, "player_id")

        # Join all mode columns
        all_player_stats_df = all_player_stats_df \
            .join(player_name_mode_df, "player_id", "left") \
            .join(player_number_mode_df, "player_id", "left") \
            .join(team_name_mode_df, "player_id", "left") \
            .join(country_name_mode_df, "player_id", "left")

        # Fill missing or placeholder values in original columns using modes
        final_player_stats = all_player_stats_df.select(
            "player_id",
            F.coalesce(F.col("player_name_mode")).alias("player_name"),
            F.coalesce(F.col("player_number_mode")).alias("player_number"),
            F.coalesce(F.col("team_name_mode")).alias("team_name"),
            F.coalesce(F.col("country_name_mode")).alias("country_name"),
            "count",
            "avg_spi_score"
        ).orderBy(desc("avg_spi_score"))

        # Save final stats to CSV
        final_player_stats.write.mode("overwrite").csv(
            f"{comp_dir}/{competition_name}_{competition_year}_player_stats_analysis.csv", header=True
        )

        print("-" * 40)
        final_player_stats.show()
        print("-" * 40)

        spark.stop()



class MVP:
    """Compute MVP rankings from per-player aggregates and render results.

    Reads the per-player analysis CSV, scales SPI (power `scalar`) and matches
    played, multiplies to `mvp_scaled`, writes full results plus a top percentile
    slice, and saves a color-graded PNG table for quick review.

    Examples:
        >>> mvp = MVP()
        >>> mvp.compute_mvp("open-cup", "2025", scalar=14)
        # writes CSVs and an image under the competition directory
    """

    def __init__(self):
        """No-op initializer for MVP computation helper.

        Examples:
            >>> MVP()
            <__main__.MVP object at ...>  # doctest: +ELLIPSIS
        """
        pass



    def __repr__(self):
        """Return a simple identifier for the MVP helper.

        Examples:
            >>> repr(MVP())  # default object repr
            '<__main__.MVP object at ...>'  # doctest: +ELLIPSIS
        """
        pass

    def compute_mvp(self, competition_name: str, competition_year: str, scalar: int=4, open_close_league:str="", title:str="", percentile_threshold:float=.98, manual_competition_id:str="", min_req_matches:bool=True)->None:
        """Compute and persist MVP rankings for a given competition/season.

        Workflow:
        - Read `<name>_<year>_player_stats_analysis.csv`.
        - Determine max matches played and max avg SPI (subject to min matches).
        - Scale SPI by `scalar` power and normalize; scale matches by max games.
        - Compute `mvp_scaled = spi_scaled * matches_scaled`.
        - Write full results and top `percentile_threshold` slice.
        - Render the top slice as a PNG table.

        Args:
            competition_name: Normalized league name.
            competition_year: Season label.
            scalar: Exponent applied to SPI before normalization (<= 100).
            open_close_league: Optional subseason label for folder naming and titles.
            title: Optional custom title for the PNG image.
            percentile_threshold: Quantile filter for the top slice (0 < p < 1).
            manual_competition_id: Optional override to disambiguate directory.
            min_req_matches: If True, require a fraction of max matches; if False, the full max.

        Returns:
            None

        Raises:
            AssertionError: If `scalar > 100` or percentile not in (0, 1).

        Examples:
            Common flow (after `Player.competition_analysis`):
            >>> MVP().compute_mvp("mls", "2025", scalar=4, title="MLS MVPs 2025", percentile_threshold=0.98, overide=False)

            Strict min-matches with manual ID:
            >>> MVP().compute_mvp("world-cup", "2018", scalar=14, manual_competition_id="77", min_req_matches=False, overide=False)
        """

        assert scalar <= 100
        spark_sess = SparkSession.builder.appName("MVPSession").getOrCreate()

        if open_close_league and not manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{open_close_league}_dir"
        elif not open_close_league and manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{manual_competition_id}_dir"
        elif open_close_league and manual_competition_id:
            comp_dir = f"{competition_name}_{competition_year}_{open_close_league}_{manual_competition_id}_dir"
        else:
            comp_dir = f"{competition_name}_{competition_year}_dir"

        all_player_stats_df = spark_sess.read.csv(f"{comp_dir}/{competition_name}_{competition_year}_player_stats_analysis.csv", header=True, inferSchema=True)

        def find_max_matches_played():
            max_games_played = all_player_stats_df.agg({"count": "max"})
            max_games_played_var = max_games_played.collect()[0]["max(count)"]
            return max_games_played_var

        def find_max_spi():
            max_avg_spi = all_player_stats_df.filter(col("count") >= min_required_matches).agg({"avg_spi_score": "max"})
            max_avg_spi_var = max_avg_spi.collect()[0]["max(avg_spi_score)"]
            return max_avg_spi_var

        max_games_played_var = find_max_matches_played()
        if not max_games_played_var:
            spark_sess.stop()
            return "No Player SPI scores are available"

        if min_req_matches:
            min_req_matches_var = 2
        else:
            min_req_matches_var = max_games_played_var

        min_required_matches = max_games_played_var / min_req_matches_var
        max_avg_spi_var = find_max_spi()
        logging.info(f"MAX GAMES PLAYED: {max_games_played_var} \n")
        logging.info(f"Max Average SPI: {max_avg_spi_var}")
        max_avg_spi_scaled_var = float(max_avg_spi_var)**scalar

        df_scaled = all_player_stats_df \
            .withColumn("spi_scaled", pyspark_round((col("avg_spi_score") ** scalar) / max_avg_spi_scaled_var, 5)) \
            .withColumn("matches_scaled", col("count") / max_games_played_var)

        mvp_df = df_scaled \
            .filter(col("count") >= min_required_matches) \
            .withColumn("mvp_scaled", col("spi_scaled") * col("matches_scaled")) \
            .sort(desc("mvp_scaled"))

        mvp_scaled_df = mvp_df.select(
            "player_name",
            "player_number",
            "team_name",
            "country_name",
            "count",
            "avg_spi_score",
            "spi_scaled",
            "matches_scaled",
            "mvp_scaled"
        )

        print("MVP DataFrame Schema", mvp_scaled_df.printSchema(), "\n")

        assert 0 < percentile_threshold < 1, "Percentile threshold must be a float between 0 and 1."
        quantile_threshold_value = mvp_scaled_df.approxQuantile("mvp_scaled", [percentile_threshold], 0.01)[0]
        filtered_percentile_df = mvp_scaled_df.filter(col("mvp_scaled") >= quantile_threshold_value).sort(desc("mvp_scaled"))
        percent_display = int(percentile_threshold * 100)
        logging.info(f"Top {100 - percent_display}% performers (>= {percent_display}th percentile threshold of {quantile_threshold_value:.5f}):")

        mvp_scaled_df.write.mode("overwrite").csv(f"{comp_dir}/{competition_name}_{competition_year}_mvp_results.csv", header=True)
        filtered_percentile_df.write.mode("overwrite").csv(f"{comp_dir}/{competition_name}_{competition_year}_mvp_top2percent.csv", header=True)

        self.save_dataframe_as_image(filtered_percentile_df.toPandas(), competition_name, competition_year, comp_dir=comp_dir, open_close_league=open_close_league, title=title)
        print(filtered_percentile_df.show())

        logging.info(f"MVP Results have been saved successfully with a scalar of {scalar}!")
        spark_sess.stop()





    def save_dataframe_as_image(self, df, competition_name, competition_year, comp_dir, open_close_league, title:str="")->None:
        """Render a Pandas DataFrame to a color-graded PNG for quick sharing.

        Saves:
            `<comp_dir>/<competition_name>_<competition_year>_mvp_results_image.png`

        Color intensity encodes `mvp_scaled`.

        Args:
            df: Pandas DataFrame with an `mvp_scaled` column and visible columns to render.
            competition_name: Normalized league name.
            competition_year: Season label.
            comp_dir: Directory to store output artifacts.
            open_close_league: Optional subseason label for title composition.
            title: Optional custom title to display above the table.

        Returns:
            None

        Examples:
            >>> # after computing MVPs and converting Spark DF to Pandas:
            >>> MVP().save_dataframe_as_image(df, "mls", "2025", "mls_2025_dir", "", title="Top 2% MLS MVPs")
        """

        image_path = f"{comp_dir}/{competition_name}_{competition_year}_mvp_results_image.png"

        # Normalize the mvp_scaled column to [0, 1]
        norm = mcolors.Normalize(vmin=df['mvp_scaled'].min(), vmax=df['mvp_scaled'].max())
         # Perceptual colormap
        cmap = cm.get_cmap('viridis') 
        row_colors = [cmap(norm(val)) for val in df['mvp_scaled']]
        # Plot setup
        fig, ax = plt.subplots(figsize=(len(df.columns) * 2, len(df) * 0.5))

        if not title and not open_close_league:
            ax.set_title(
                f"Top 2% MVPs for {competition_name.upper()} in {competition_year}",
                fontsize=16, fontweight='bold', pad=20
            )
        elif not title:
            ax.set_title(
                f"Top 2% MVPs for {competition_name.upper()} in {open_close_league} {competition_year}",
                fontsize=16, fontweight='bold', pad=20
            )
        else:
            ax.set_title(
                f"{title}",
                fontsize=16, fontweight='bold', pad=20
            )
        ax.axis('off')
        # Table setup
        table = ax.table(cellText=df.values,
                        colLabels=df.columns,
                        loc='center',
                        cellLoc='center')
        # Style header
        for col_idx, col in enumerate(df.columns):
            header_cell = table[0, col_idx]
            header_cell.set_fontsize(12)
            header_cell.set_text_props(weight='bold', color='white')
            header_cell.set_facecolor('#333333')
        # Style body cells with gradient color
        for row_idx, row_color in enumerate(row_colors, start=1):  # row 0 is header
            luminance = mcolors.rgb_to_hsv(row_color[:3])[2]
            text_color = 'black' if luminance > 0.6 else 'white'
            for col_idx in range(len(df.columns)):
                cell = table[row_idx, col_idx]
                cell.set_facecolor(row_color)
                cell.get_text().set_color(text_color)
        # Save image
        plt.savefig(image_path, bbox_inches='tight', dpi=300)
        plt.close()
        logging.info(f"Saved dataframe image to {image_path}")



def workflow_compute_mvp(competition_name: str, competition_year: int, scalar: int=4, open_close_league:str="", overide:bool=True, title:str="", percentile_threshold:float=.98, manual_competition_id:str="", min_req_matches:bool=True)->str:
    """Run the full MVP pipeline end-to-end for a given league and season.

    Steps:
    1) (Optional) Resolve competition and write match URLs (`Competition`).
    2) Scrape match stats and persist per-match player stats (`Match`).
    3) Expand per-appearance rows into flat player stats (`Player`).
    4) Aggregate per-player metrics (`Player.competition_analysis`).
    5) Compute MVP rankings and render outputs (`MVP`).

    Args:
        competition_name: Normalized league name (e.g., "premier-league").
        competition_year: Season label (e.g., 2023).
        scalar: Exponent used to scale SPI impact (default 4).
        open_close_league: Optional subseason label (e.g., "Apertura").
        overide: If True, always re-scrape match links; else resume incomplete runs.
        title: Optional custom title for the MVP image.
        percentile_threshold: Quantile (0–1) to select the top slice (default 0.98).
        manual_competition_id: Optional manual override for competition ID.
        min_req_matches: If True, require only a fraction of max matches; else strict.

    Returns:
        str: Completion message, or guidance if the competition must be added first.

    Examples:
        Quick start:
        >>> all_comps = AllCompetitions()
        >>> ids = all_comps.gather_all_competition_ids("https://www.fotmob.com/leagues")  # run
        >>> all_comps.add_competition_to_my_watchlist("open-cup", ids)
        >>> workflow_compute_mvp("open-cup", 2025, scalar=14, overide=False)
        'Most Valuable Player has been unvailed from competition open-cup during the year 2025'
    """
    competition_year = str(competition_year)

    comps = Competition()
    if overide:
        comp_bool = comps.choose_competition(competition_name, competition_year, open_close_league, manual_competition_id) # run

        if not comp_bool:
            return """
                Competition must be added first. See example:
                all_comps = AllCompetitions()
                all_comp_info = all_comps.gather_all_competition_ids("https://www.fotmob.com/") # run
                print(all_comp_info)
                print(all_comps.add_competition_to_my_watchlist("champions-league", all_comp_info))
                """
        
    match = Match()
    logging.info(match.choose_match(competition_name, competition_year, open_close_league, overide, manual_competition_id=manual_competition_id)) # run
    player = Player()
    logging.info(player.choose_player_stats(competition_name, competition_year, open_close_league, manual_competition_id=manual_competition_id)) # run both 
    logging.info(player.competition_analysis(competition_name, competition_year, open_close_league, manual_competition_id=manual_competition_id)) # run both
    mvp = MVP()
    logging.info(mvp.compute_mvp(competition_name, competition_year, scalar=scalar, open_close_league=open_close_league, title=title, percentile_threshold=percentile_threshold, manual_competition_id=manual_competition_id, min_req_matches=min_req_matches)) 
    return f"Most Valuable Player has been unvailed from competition {competition_name} during the year {competition_year}"















# if __name__ == "__main__":
# #     # Workflow 1A - add a competetion
#     all_comps = AllCompetitions()
#     all_comp_info = all_comps.gather_all_competition_ids("https://www.fotmob.com/") # run
#     print(all_comp_info)

#     # Sample Test 1
#     print(all_comps.add_competition_to_my_watchlist(competition_name="fifa-intercontinental-cup", gather_all_competition_ids=all_comp_info))
#     print(workflow_compute_mvp(competition_name="fifa-intercontinental-cup", competition_year="2024", scalar=14, min_req_matches=False))

# #     # Sample Test 2
# #     print(all_comps.add_competition_to_my_watchlist(competition_name="world-cup", gather_all_competition_ids=all_comp_info, defined_url="https://www.fotmob.com/leagues/77/matches/world-cup"))#     # print(workflow_compute_mvp(competition_name="world-cup", competition_year="2010", manual_competition_id="77", scalar=14, min_req_matches=False))
# #     print(workflow_compute_mvp(competition_name="world-cup", competition_year="2014", manual_competition_id="77", scalar=14, min_req_matches=False))
# #     print(workflow_compute_mvp(competition_name="world-cup", competition_year="2018", manual_competition_id="77", scalar=14))
# #     print(workflow_compute_mvp(competition_name="world-cup", competition_year="2022", manual_competition_id="77", scalar=14))

# #     # Sample Test 3
#     print(all_comps.add_competition_to_my_watchlist(competition_name="mls", gather_all_competition_ids=all_comp_info))
#     print(workflow_compute_mvp(competition_name="mls", competition_year="2025", scalar=4))
