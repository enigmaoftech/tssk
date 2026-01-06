<p align="center">
   <img width="567" height="204" alt="Image" src="https://github.com/user-attachments/assets/35eae37f-606c-4fbb-b063-fe80584e8af9" />
</p>

TSSK (TV Show Status for Kometa) checks [Sonarr](https://sonarr.tv/) for your TV Shows statuses and creates .yml files<br>
which can be used by [Kometa](https://kometa.wiki/) to create collections and overlays.</br>


Categories:
*  New shows, that were added in the past x days
*  Shows with upcoming regular episodes within x days
*  Shows for which a new season is airing within x days
*  Shows for which a new season has been added which aired in the past x days
*  Shows with upcoming season finales within x days
*  Shows for which a season finale was added which aired in the past x days
*  Shows for which a final episode was added which aired in the past x days

---

## 📝 Table of Contents
* [✨ Features](#-features)
* [🛠️ Installation](#-installation)
* [🧩 Continue Setup](#-continue-setup)
    * [1️⃣ Edit your Kometa config](#1-edit-your-kometa-config)
    * [2️⃣ Edit your configuration file](#2-edit-your-configuration-file)
* [⚙️ Configuration](#-configuration)
* [🚀 Usage](#-usage)
* [⚠️ Do you Need Help or have Feedback?](#️-do-you-need-help-or-have-feedback)
  
---

## ✨ Features
- 🗓️ **Detects upcoming episodes, finales and seasons**: Searches Sonarr for TV show schedules.
- 🏁 **Aired Finale labelling**: Use a separate overlay for shows for which a Finale was added.
-  ▼ **Filters out unmonitored**: Skips show if season/episode is unmonitored. (optional)
-  🪄 **Customizable**: Change date format, collection name, overlay positioning, text, ..
- ℹ️ **Informs**: Lists matched and skipped(unmonitored) TV shows.
- 📝 **Creates .yml**: Creates collection and overlay files which can be used with Kometa.

---

## 🛠️ Installation

1. Ensure you have [Docker](https://docs.docker.com/get-docker/) installed.

2. Copy the example environment file and configure it:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` with your settings. See [`.env.example`](.env.example) for the complete list of available environment variables.

3. Review and customize the `docker-compose.yml` file if needed. See [`docker-compose.yml`](docker-compose.yml) for the complete configuration.

4. Run the container:
```sh
docker compose up -d
```

This will:
- Build the TSSK container with Python scheduler
- Run the script on a daily schedule (by default at 2AM)
- Mount your configuration and output directories into the container

You can customize the run schedule by modifying the `APP_TIMES` environment variable in your `.env` file (format: `HH:MM`, e.g., `02:00` for 2 AM, or `02:00,14:00` for multiple times).

---

## 🧩 Continue Setup

### 1️⃣ Edit your Kometa config

Open your **Kometa** config.yml (typically at `/config/config.yml`, NOT your TSSK config file).

The `.yml` files created by TSSK that Kometa uses are saved to `/config/tssk/` inside the container — assuming you mount your Kometa config folder to `/config`.

Make sure your Kometa config uses the correct path to reference those files.

In your Kometa config, include paths to the generated .yml files under your `TV Shows` library:

```yaml
TV Shows:
  collection_files:
  - file: /config/tssk/TSSK_TV_NEW_SEASON_COLLECTION.yml
  - file: /config/tssk/TSSK_TV_NEW_SEASON_STARTED_COLLECTION.yml
  - file: /config/tssk/TSSK_TV_UPCOMING_EPISODE_COLLECTION.yml
  - file: /config/tssk/TSSK_TV_UPCOMING_FINALE_COLLECTION.yml
  - file: /config/tssk/TSSK_TV_FINAL_EPISODE_COLLECTION.yml
  - file: /config/tssk/TSSK_TV_SEASON_FINALE_COLLECTION.yml
  overlay_files:
  - file: /config/tssk/TSSK_TV_NEW_SEASON_OVERLAYS.yml
  - file: /config/tssk/TSSK_TV_NEW_SEASON_STARTED_OVERLAYS.yml
  - file: /config/tssk/TSSK_TV_UPCOMING_EPISODE_OVERLAYS.yml
  - file: /config/tssk/TSSK_TV_UPCOMING_FINALE_OVERLAYS.yml
  - file: /config/tssk/TSSK_TV_FINAL_EPISODE_OVERLAYS.yml
  - file: /config/tssk/TSSK_TV_SEASON_FINALE_OVERLAYS.yml
```

> [!TIP]
> Only add the files for the categories you want to enable. All are optional and independently generated based on your config settings. 

### 2️⃣ Edit your configuration file
---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file by copying the example file:
```bash
cp .env.example .env
```

Then edit `.env` with your configuration. For the complete and up-to-date list of all environment variables, see [`.env.example`](.env.example).

**Required variables:**
- **SONARR_URL:** Your Sonarr instance URL (e.g., `http://localhost:8989`)
- **SONARR_API_KEY:** Your Sonarr API key (found in Sonarr under Settings => General => Security)

**Optional variables:**
- **SONARR_TIMEOUT:** Request timeout in seconds (default: `90`)
- **TZ:** Timezone (e.g., `America/New_York`)
- **PUID/PGID:** User/Group IDs for file permissions (default: `1000`)
- **APP_TIMES:** Schedule times in HH:MM format (default: `02:00`)
- **RUN_AT_START:** Run immediately on startup (default: `true`)

> [!NOTE]
> Always refer to [`.env.example`](.env.example) for the latest environment variable options and defaults.

### Config File

Rename `data/config.example.yml` to `data/config.yml` and edit the needed settings:

- **log_retention_runs:** Number of previous log runs to keep (default: `7`). Logs are automatically rotated and compressed.
- **skip_unmonitored:** Default `false` if set to true it will skip a show if the upcoming season/episode is unmonitored.
- **ignore_finales_tags:** Shows with these tags will be ignored when checking for finales.
>[!NOTE]
> For some shows, episodes are listed one at a time usually one week ahead in Sonarr. Because of this, TSSK wrongly (yet logically..) thinks that the last episode listed in the season is a finale.
> You can give problematic shows like this a tag in Sonarr so TSSK will ignore finales for that show and treat the current 'last' episode of the season as a regular episode.

>[!NOTE]
> Timezone is set via the `TZ` environment variable in your `.env` file (e.g., `TZ=America/New_York`). The script will automatically use this timezone for all date calculations and conversions.

- **simplify_next_week_dates:** Will simplify dates to `today`, `tomorrow`, `friday` etc if the air date is within the coming week.
- **process_:** Choose which categories you wish to process. Change to `false` to disable.

For each category, you can change the relevant settings:
- **future_days:** How many days into the future the script should look.
- **recent_days:** How many days in the past the script should look (for aired Finales)

- **collection block:**
  - **collection_name:** The name of the collection.
  - **smart_label:** Choose the sorting option. [More info here](https://metamanager.wiki/en/latest/files/builders/smart/#sort-options)
  - **sort_title:** Collection sort title.
  - etc
>[!TIP]
>You can enter any other Kometa variables in this block and they will be automatically added in the generated .yml files.</br>
>`collection_name` is used to name the collection and will be stripped from the collection block.
  
- **backdrop block:**
  - **enable:** whether or not you want a backdrop (the colored banner behind the text)
  - Change backdrop size, color and positioning. You can add any relevant variables here. [More info here](https://kometa.wiki/en/latest/files/overlays/?h=overlay#backdrop-overlay)
    
- **text block:** 
  - **date_format:** The date format to be used on the overlays. e.g.: "yyyy-mm-dd", "mm/dd", "dd/mm", etc.
  - **capitalize_dates:** `true` will capitalize letters in dates.
  - **use_text:** Text to be used on the overlays before the date. e.h.: "NEW SEASON"
  - Change text color and positioning. You can add any relevant variables here. [More info here](https://kometa.wiki/en/latest/files/overlays/?h=overlay#text-overlay)
  - For `New Season Soon`, `New Season Started`, `Upcoming Finale` and `Season Finale` you can use [#] to display the season number

> [!TIP]
> `group` and `weight` are used to determine which overlays are applied in case multiple are valid.
> Example: You add a new show, for which season 2 just aired in full yesterday. In this case the following overlays would be valid: `new show`, `new season` and `season finale`.
> In the default config, `new show` has the highest weight (40) so that's the overlay that will be applied. If you prefer any of the other to be applied instead, you need to increase their weight.
> You can also choose to have multiple overlays applied at the same time by removing the group and weight, in case you put them in different positions.


>[!NOTE]
> These are date formats you can use:<br/>
> `d`: 1 digit day (1)<br/>
> `dd`: 2 digit day (01)<br/>
> `ddd`: Abbreviated weekday (Mon)<br/>
> `dddd`: Full weekday (Monday)<br/>
><br/>
> `m`: 1 digit month (1)<br/>
> `mm`: 2 digit month (01)<br/>
> `mmm`: Abbreviated month (Jan)<br/>
> `mmmm`: Full month (January)<br/>
><br/>
> `yy`: Two digit year (25)<br/>
> `yyyy`: Full year (2025)
>
>Dividers can be `/`, `-` or a space

---
## 🚀 Usage

The script runs automatically according to the schedule defined by the `APP_TIMES` environment variable in your `.env` file (default: `02:00` for 2 AM daily). See [`docker-compose.yml`](docker-compose.yml) for the complete Docker configuration.  
You can inspect the container logs to see output and monitor activity:

```sh
docker logs -f tssk
```

The script will list matched and/or skipped shows and create the .yml files.  
The previous configuration will be erased so Kometa will automatically remove overlays for shows that no longer match the criteria.

---

### ⚠️ **Original project can be found here**
- https://github.com/netplexflix/TV-show-status-for-Kometa
