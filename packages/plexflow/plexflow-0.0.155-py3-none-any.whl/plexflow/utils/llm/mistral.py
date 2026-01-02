from mistralai import Mistral
from io import StringIO
from plexflow.utils.strings.json_extract import extract_json_from_string

def extract_torrents(content: str, **kwargs):
    api_key = kwargs.get("api_key", "bZ6vS0p30hiEqpyy6fBZUMyuZuiqaS91")
    model = kwargs.get("model", "mistral-large-latest")

    client = Mistral(api_key=api_key)

    stream_response = client.chat.stream(
        model = model,
        messages = [
            {
                "role": "user",
                "content": f"""
                Parse the torrents as JSON, designate the total seeds as the field 'seeds', the total peers as the field 'peers', the date added as the field 'date', the torrent title as 'title', the torrent size as 'size', the torrent category as 'category', keep all other fields the same:

                {content}
                """,
            },
        ]
    )

    buffer = StringIO()

    for chunk in stream_response:
        chunk = chunk.data.choices[0].delta.content
        if kwargs.get("log", False):
            print(chunk, end="")
        
        buffer.write(chunk)
    
    json_data = buffer.getvalue()
    
    return extract_json_from_string(json_data)


torrents = extract_torrents(
    """


Login
Home
Catalog
Box Office
New Selection
4K Movies
4K XXX
 Home  Movies  TV  Games  Music  Anime  Apps  Other  Books  XXX  Pages
XXX content
Search title or IMDB ID like tt27932269 ...

»
Reset
My 30 Books March 3 2 mature maturenl tt0051532 girlsoutwest Audiobooks heavier trip matrix language issue mummy The Office nacho libre the gentlemen playboyplus the flash 2023 The Comeback The Lord of the Rings twin peaks 720p the work 1080p vikings Windows All 7 8 1 10 11 All Editions With Updates AIO 46in1 glass 2019 Thunderbolts ma the invasion Becastled v0 6002 naughtyamericavr DesignOptimal Editable font and
Mufasa: The Lion King 2024
 Play

Title: Mufasa: The Lion King
EXTERNAL URL: IMDB | TMDB
Languages: English
Genres: Animation, Adventure, Drama, Family, Fantasy, Musical,
Runtime: 2:00:00 Hour
Cast: Aaron Pierre, Kelvin Harrison Jr., Tiffany Boone
Directors: Barry Jenkins
IMDB Rating Rating: 6.8 (1406 Votes)
Year: 2024
Summary: Mufasa, a cub lost and alone, meets a sympathetic lion named Taka, the heir to a royal bloodline. The chance meeting sets in motion an expansive journey of a group of misfits searching for their destiny.
:TRAILER:

Search table...
C	File	Category	Added	Time	Size	Se.	Le.
	
Mufasa The Lion King 2024 720p WEBRiP x264 XoXo M.Q.A
Movies	2025-02-02	8 hours	4.0 GB	26	50
	
Mufasa The Lion King 2024 1080p WEBRiP x264 XoXo M.Q.A
Movies	2025-02-02	8 hours	8.4 GB	40	34
	
Mufasa The Lion King 2024 720p WEB DL 2000MB Feranki1980 M.Q.A
Movies	2025-01-09	3 weeks, 2 days	2.0 GB	44	22
	
Mufasa The Lion King 2024 1080p WEBRip Multi AAC x265 HNY M.Q.A
Movies	2025-01-02	1 month	1.5 GB	43	48
	
Mufasa The Lion King 2024 1080P WEBRiP 24 bit Stereo HEVC X265 POOTLED mkv M.Q.A
Movies	2025-01-02	1 month	3.1 GB	23	33
	
Mufasa The Lion King 2024 1080p WEBRip x265 10bit YTS M.Q.A
Movies	2025-01-02	1 month	1.7 GB	294	621
	
Mufasa The Lion King 2024 1080p WEBRIP H264 HAPPYNEWYEAR COLLECTi M.Q.A
Movies	2025-01-02	1 month	3.7 GB	35	42
	
Mufasa The Lion King 2024 1080p WEBRip YTS M.Q.A
Movies	2025-01-01	1 month	1.8 GB	424	1301
	
Mufasa Il Re Leone 2024 1080p HDRip HQ h264 ADS MD Ita iDN_Cr M.Q.A
Movies	2025-01-01	1 month	2.5 GB	36	10
	
Mufasa The Lion King 2024 720p WEBRip YTS M.Q.A
Movies	2025-01-01	1 month	1020.6 MB	422	796
	
Mufasa The Lion King 2024 1080p WEBRIP H264 HAPPYNEWYEAR COLLECTiVE M.Q.A
Movies	2025-01-01	1 month	3.7 GB	45	37
	
Mufasa The Lion King 2024 1080p WEBRip READNFO x265 AC3 AOC M.Q.A
Movies	2024-12-31	1 month	5.9 GB	13	13
	
Mufasa The Lion King 2024 1080p HDRip ENG HappyNEWYear M.Q.A
Movies	2024-12-31	1 month	2.5 GB	95	714
	
Mufasa The Lion King 2024 1080p Cam X264 COLLECTiVE M.Q.A
Movies	2024-12-23	1 month, 1 week	3.7 GB	27	21
	
Mufasa The Lion King 2024 V 2 1080p HDTS C1NEM4 M.Q.A
Movies	2024-12-20	1 month, 2 weeks	2.1 GB	14	45
	
Mufasa The Lion King 2024 HDCAM c1nem4 x264 SUNSCREEN TGx M.Q.A
Movies	2024-12-20	1 month, 2 weeks	995.1 MB	12	25
	
Mufasa The Lion King 2024 720p HDCAM C1NEM4 M.Q.A
Movies	2024-12-20	1 month, 2 weeks	1.7 GB	14	19
Showing 1 to 17 of 17 entries
    """,
    log=False
)

if len(torrents) == 0:
    print("No torrents found")
else:
    if type(torrents[0]) == list:
        torrents = torrents[0]
    
    print(len(torrents), "torrents found")

    for torrent in torrents:
        print(torrent)
