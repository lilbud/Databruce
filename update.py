"""
Project Name: Databruce
Author Name: Lilbud
Name: Update
File Purpose: Updates the Database file, uses the functions in Data_Collection
"""

import time
import datetime
from data_collection import (
    get_bands,
    get_people,
    get_songs,
    get_venues,
    get_tours,
    setlist_to_events,
)
from data_collection import (
    get_albums,
    get_events_by_year,
    get_tour_events,
    get_show_info,
)
from data_collection import conn, cur
from helper_stuff import run_time

main_url = "http://brucebase.wikidot.com/"
current_year = int(datetime.datetime.now().date().strftime("%Y"))
start_time = datetime.datetime.now()
current_date = datetime.datetime.now(tz=datetime.timezone.utc)


def update_counts():
    """update various play/performance counts"""
    for s in cur.execute("""SELECT song_url, song_name FROM SONGS""").fetchall():
        count = cur.execute(
            f"""SELECT COUNT(\"{s[0]}\"), MIN(event_url), MAX(event_url) FROM SETLISTS WHERE song_url = \"{s[0]}\" AND set_type NOT LIKE '%Rehearsal%' AND set_type NOT LIKE '%Soundcheck%' AND set_type NOT LIKE '%No Bruce%'"""
        ).fetchone()
        total = cur.execute(
            """SELECT COUNT(event_id) FROM EVENTS WHERE event_url LIKE '/gig:%'"""
        ).fetchone()

        if count[0] > 0:
            opener = cur.execute(
                f"""SELECT COUNT(event_url) FROM EVENTS WHERE setlist LIKE '{s[1].replace("'", "''")}, %'"""
            ).fetchone()

            closer = cur.execute(
                f"""SELECT COUNT(event_url) FROM EVENTS WHERE setlist LIKE '%, {s[1].replace("'", "''")}'"""
            ).fetchone()

            frequency = f"{round(((count[0] / total[0]) * 100), 2)}"

            cur.execute(
                f"""UPDATE SONGS SET num_plays='{count[0]}', first_played='{count[1]}', last_played='{count[2]}', frequency='{frequency}', opener='{opener[0]}',closer='{closer[0]}' WHERE song_url=\"{s[0]}\""""
            )
        else:
            count = first_played = last_played = opener = closer = frequency = ""
            cur.execute(
                f"""UPDATE SONGS SET num_plays='{count}', first_played='{first_played}', last_played='{last_played}', frequency='{frequency}', opener='{opener}',closer='{closer}' WHERE song_url=\"{s[0]}\""""
            )

        conn.commit()

    print("Song Count Updated")

    for v in cur.execute("""SELECT venue_url FROM VENUES""").fetchall():
        count = cur.execute(
            f"""SELECT COUNT(\"{v[0]}\") FROM EVENTS WHERE location_url=\"{v[0]}\""""
        ).fetchone()
        cur.execute(
            f"""UPDATE VENUES SET num_performances={count[0]} WHERE venue_url=\"{v[0]}\""""
        )
        conn.commit()

    print("Venue Count Updated")

    for r in cur.execute("""SELECT relation_url FROM RELATIONS""").fetchall():
        count = cur.execute(
            f"""SELECT COUNT(\"{r[0]}\") FROM ON_STAGE WHERE relation_url=\"{r[0]}\""""
        ).fetchone()
        cur.execute(
            f"""UPDATE RELATIONS SET appearances={count[0]} WHERE relation_url=\"{r[0]}\""""
        )
        conn.commit()

    print("band and person count updated")

    for t in cur.execute("""SELECT tour_url, tour_name FROM TOURS""").fetchall():
        count = cur.execute(
            f"""SELECT COUNT(\"{t[1]}\"), MIN(event_url), MAX(event_url) FROM EVENTS WHERE tour=\"{t[1]}\" AND event_url LIKE '/gig:%'"""
        ).fetchone()

        # id_sql = "', '".join(str(x[0].replace("'", "''")) for x in cur.execute(f"""SELECT event_date FROM EVENTS WHERE tour='{t[1].replace("'", "''")}' AND event_url LIKE '/gig:%'""").fetchall())
        song_count = cur.execute(
            f"""SELECT COUNT(DISTINCT(song_name)) FROM SETLISTS WHERE event_url IN (SELECT event_url FROM EVENTS WHERE tour='{t[1].replace("'", "''")}' AND event_url LIKE '/gig:%')"""
        ).fetchone()[0]

        cur.execute(
            f"""UPDATE TOURS SET num_shows={count[0]}, first_show='{str(count[1])}', last_show='{str(count[2])}', num_songs={song_count} WHERE tour_url=\"{t[0]}\""""
        )
        conn.commit()

    print("Tour Event Count Updated")


def update_premiere_debut():
    """updates each setlist and marks if each song is a premiere or debut"""

    # for e in cur.execute(f"""SELECT event_url FROM SETLISTS WHERE event_url LIKE '/gig:%'""").fetchall():
    # 	print(e)


# update_premiere_debut()


def basic_update(start_year):
    """builds the database, gets the basic amount of information"""

    get_bands()
    get_people()
    get_songs()
    get_venues()
    get_tours()
    get_albums()

    for i in range(1965, current_year + 1):
        get_events_by_year(i)
        cur.execute("""vacuum;""")
        time.sleep(1)

    for t in cur.execute("""SELECT tour_url, tour_name FROM TOURS""").fetchall():
        get_tour_events(t[0], t[1])
        print(t[1])
        time.sleep(1)

    # uncomment the below lines if running both basic and full update
    # print("Sleeping for 5 seconds")
    # time.sleep(5)


def full_update(start, end):
    """gets show info for all events in events table"""

    delay = 0

    # get_bootlegs()
    # get_official_live()

    for i in range(start, end + 1):
        print(i)

        # for u in cur.execute(f"""SELECT event_url FROM EVENTS WHERE event_date LIKE '{str(i)}%' AND date(event_date) < date('now', '+1 days')""").fetchall():
        for u in cur.execute(
            f"""SELECT event_url FROM EVENTS WHERE event_date LIKE '{str(i)}%' AND event_date <= '{current_date.date()}'"""
        ).fetchall():
            setcheck = cur.execute(
                f"""SELECT EXISTS(SELECT 1 FROM SETLISTS WHERE event_url LIKE '%{u[0]}%' LIMIT 1)"""
            ).fetchone()

            if setcheck[0] == 0:
                get_show_info(u[0])
                print(u[0])
                time.sleep(0.5)
                delay = 2

        if start != end:
            print(f"Sleeping for {delay} seconds")
            time.sleep(delay)
            cur.execute("""vacuum;""")


# basic_update()
# usually can just be run for the current year
# get_official_live()

# winsound.Beep(1500, 250)

if __name__ == "__main__":
    get_songs()
    full_update(current_year, current_year)
    setlist_to_events()
    update_counts()
    run_time(start_time)
