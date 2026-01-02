import json
import re

def extract_json_from_string(text):
    """
    Extracts JSON objects from a string.  Handles multiple JSON objects 
    and ignores invalid JSON parts.

    Args:
        text: The input string potentially containing JSON.

    Returns:
        A list of dictionaries, where each dictionary represents a 
        valid JSON object found in the string. Returns an empty list
        if no valid JSON is found.
    """

    json_objects = []
    # Regular expression to find potential JSON objects (improved)
    # This looks for curly braces and square brackets to identify 
    # potential JSON structures.  It's not perfect, but it's a reasonable
    # starting point.
    json_matches = re.finditer(r"\[.*?\]|\{.*?\}", text, re.DOTALL)  # DOTALL makes . match newlines

    for match in json_matches:
        try:
            json_object = json.loads(match.group(0))  # Attempt to parse
            json_objects.append(json_object)
        except json.JSONDecodeError:
            # If parsing fails, it wasn't valid JSON, so we ignore it.
            pass  # or print(f"Invalid JSON found: {match.group(0)}") for debugging

    return json_objects


if __name__ == "__main__":
    raw = """
    Sure, here is the JSON representation of the parsed torrents with the specified fields:

    ```json
    [
        {
            "title": "Wicked.2024.UHD.BluRay.2160p.TrueHD.Atmos.7.1.DV.HEVC.REMUX-FraMeSToR",
            "category": "Movies : 4K UHD",
            "language": "English",
            "size": "77.22 GB",
            "seeds": 2,
            "peers": 1856,
            "date": "30/01/25 06:17",
            "uploader": "JackONeill:_verified_uploader:",
            "S/L": "[214/399]"
        },
        {
            "title": "Wicked.2024.1080p.Bluray.DDP7.1.HEVC.x265-BluBirD",
            "category": "Movies : HD",
            "language": "English",
            "size": "6.63 GB",
            "seeds": 0,
            "peers": 537,
            "date": "29/01/25 23:57",
            "uploader": "Nick007:_trusted_uploader:",
            "S/L": "[419/70]"
        },
        {
            "title": "Wicked.2024.1080p.BluRay.AAC5.1 [YTS]",
            "category": "Movies : HD",
            "language": "English",
            "size": "2.95 GB",
            "seeds": 0,
            "peers": 396,
            "date": "29/01/25 22:00",
            "uploader": "indexFroggy:_trusted_uploader:",
            "S/L": "[679/217]"
        },
        {
            "title": "Wicked.2024.1080p.WEBRip.x265.10bit.AAC5.1 [YTS]",
            "category": "Movies : HD",
            "language": "English",
            "size": "2.70 GB",
            "seeds": 1,
            "peers": 3757,
            "date": "29/01/25 20:09",
            "uploader": "indexFroggy:_trusted_uploader:",
            "S/L": "[3,483/574]"
        },
        {
            "title": "Wicked.2024.720p.BluRay [YTS]",
            "category": "Movies : HD",
            "language": "English",
            "size": "1.44 GB",
            "seeds": 0,
            "peers": 337,
            "date": "29/01/25 20:00",
            "uploader": "indexFroggy:_trusted_uploader:",
            "S/L": "[305/178]"
        },
        {
            "title": "Wicked.2024.1080p.Blu-ray.Remux.AVC.TrueHD.Atmos.7.1-CiNEPHiLES",
            "category": "Movies : HD",
            "language": "English",
            "size": "31.79 GB",
            "seeds": 0,
            "peers": 593,
            "date": "29/01/25 15:01",
            "uploader": "JackONeill:_verified_uploader:",
            "S/L": "[111/40]"
        },
        {
            "title": "Wicked.(2024).1080p.DS4K.10bit.AMZN.WEBRip.DDP.5.1.Atmos.x265-DE3PM.",
            "category": "Movies : HD",
            "language": "Hindi",
            "size": "6.06 GB",
            "seeds": 0,
            "peers": 933,
            "date": "15/01/25 05:43",
            "uploader": "DE3PM:_verified_uploader:",
            "S/L": "[28/20]"
        },
        {
            "title": "Wicked.2024.2160p.WEB-DL.DDP5.1.Atmos.DV.H.265.MP4",
            "category": "Movies : 4K UHD",
            "language": "English",
            "size": "28.52 GB",
            "seeds": 2,
            "peers": 1991,
            "date": "11/01/25 11:16",
            "uploader": "VarroaD:_verified_uploader:",
            "S/L": "[27/32]"
        },
        {
            "title": "Wicked (2024) DS4K 1080p MA WEBRip AV1 Opus 5.1 [RAV1NE]",
            "category": "Movies : HD",
            "language": "English",
            "size": "3.19 GB",
            "seeds": 1,
            "peers": 1886,
            "date": "06/01/25 15:26",
            "uploader": "RAV1NE:_trusted_uploader:",
            "S/L": "[147/33]"
        },
        {
            "title": "Wicked.2024.1080p.WEBRip.AAC5.1 [YTS]",
            "category": "Movies : HD",
            "language": "English",
            "size": "2.95 GB",
            "seeds": 0,
            "peers": 8320,
            "date": "05/01/25 19:26",
            "uploader": "indexFroggy:_trusted_uploader:",
            "S/L": "[817/135]"
        },
        {
            "title": "Wicked.2024.720p.WEBRip [YTS]",
            "category": "Movies : HD",
            "language": "English",
            "size": "1.44 GB",
            "seeds": 0,
            "peers": 1881,
            "date": "05/01/25 17:23",
            "uploader": "indexFroggy:_trusted_uploader:",
            "S/L": "[36/157]"
        },
        {
            "title": "Wicked.2024.DUAL-AUDiO.SPA-ENG.2160p.WEB-DL.DV.DDP5.1.HDR10Plus.H.265-DMnT",
            "category": "Movies : 4K UHD",
            "language": "Other / Multiple",
            "size": "28.84 GB",
            "seeds": 0,
            "peers": 1557,
            "date": "04/01/25 17:25",
            "uploader": "outr0x:_trusted_uploader:",
            "S/L": "[40/106]"
        },
        {
            "title": "Wicked.2024.DUAL-AUDiO.SPA-ENG.1080p.WEB-DL.DDP5.1.H.264-DMnT",
            "category": "Movies : HD",
            "language": "Other / Multiple",
            "size": "11.81 GB",
            "seeds": 0,
            "peers": 657,
            "date": "04/01/25 17:24",
            "uploader": "outr0x:_trusted_uploader:",
            "S/L": "[40/79]"
        },
        {
            "title": "Wicked.2024.1080p.MA.WEB-DL.DDP5.1.Atmos.H.264-FLUX.mkv",
            "category": "Movies : HD",
            "language": "English",
            "size": "9.70 GB",
            "seeds": 0,
            "peers": 1985,
            "date": "03/01/25 08:31",
            "uploader": "platypusp:_trusted_uploader:",
            "S/L": "[86/17]"
        },
        {
            "title": "Wicked.2024.2160p.WEBRip.x265.10bit.AAC5.1 [YTS]",
            "category": "Movies : 4K UHD",
            "language": "English",
            "size": "7.20 GB",
            "seeds": 0,
            "peers": 6310,
            "date": "03/01/25 04:43",
            "uploader": "indexFroggy:_trusted_uploader:",
            "S/L": "[1,418/260]"
        },
        {
            "title": "Wicked (2024) 1080p WEBDL H264 Subs - LoZio .mkv",
            "category": "Movies : HD",
            "language": "English",
            "size": "4.22 GB",
            "seeds": 1,
            "peers": 1614,
            "date": "01/01/25 15:19",
            "uploader": "LoZio:_trusted_uploader:",
            "S/L": "[53/14]"
        },
        {
            "title": "Wicked.2024.1080p.AMZN.WEB-DL.x264.ESubs.[2.4GB].[MP4]",
            "category": "Movies : HD",
            "language": "English",
            "size": "2.45 GB",
            "seeds": 0,
            "peers": 4747,
            "date": "01/01/25 04:24",
            "uploader": "cutee143:_trusted_uploader:",
            "S/L": "[137/92]"
        },
        {
            "title": "Wicked.2024.720p.AMZN.WEB-DL.x264.ESubs.[1.3GB].[MP4]",
            "category": "Movies : HD",
            "language": "English",
            "size": "1.32 GB",
            "seeds": 1,
            "peers": 7919,
            "date": "31/12/24 19:56",
            "uploader": "cutee143:_trusted_uploader:",
            "S/L": "[348/197]"
        },
        {
            "title": "Wicked. 2024. 1080P. AMZN WEB-DL. DDP5.1. HEVC-X265. POOTLED.mkv",
            "category": "Movies : HD",
            "language": "English",
            "size": "4.49 GB",
            "seeds": 0,
            "peers": 2323,
            "date": "31/12/24 17:58",
            "uploader": "Pootle:_trusted_uploader:",
            "S/L": "[39/21]"
        },
        {
            "title": "Wicked 2024 1080p WEB-DL HEVC x265 5.1 BONE",
            "category": "Movies : HD",
            "language": "English",
            "size": "1.99 GB",
            "seeds": 7,
            "peers": 16187,
            "date": "31/12/24 17:32",
            "uploader": "B0NE:_trusted_uploader::_sitefriend:",
            "S/L": "[430/361]"
        },
        {
            "title": "Wicked 2024 720p AMZN WEBRip English Hindi AAC 5.1 ESubs x264 - mkvAnime.mkv",
            "category": "Movies : HD",
            "language": "Hindi",
            "size": "1.69 GB",
            "seeds": 0,
            "peers": 685,
            "date": "31/12/24 16:15",
            "uploader": "LOKiHD:_verified_uploader::_sitefriend:",
            "S/L": "[1/21]"
        },
        {
            "title": "Wicked.2024.Hybrid.2160p.WEB-DL.DV.HDR.DDP5.1.H265-AOC",
            "category": "Movies : 4K UHD",
            "language": "English",
            "size": "28.89 GB",
            "seeds": 3,
            "peers": 10753,
            "date": "31/12/24 15:58",
            "uploader": "atomicfusion:_trusted_uploader:",
            "S/L": "[561/825]"
        },
        {
            "title": "Wicked.2024.2160p.WEB-DL.DDP5.1.SDR.H265-AOC",
            "category": "Movies : 4K UHD",
            "language": "English",
            "size": "17.91 GB",
            "seeds": 2,
            "peers": 5464,
            "date": "31/12/24 15:58",
            "uploader": "atomicfusion:_trusted_uploader:",
            "S/L": "[210/194]"
        },
        {
            "title": "Wicked.2024.1080p.WEB-DL.x264.6CH.Dual.YG⭐",
            "category": "Movies : HD",
            "language": "Spanish",
            "size": "3.55 GB",
            "seeds": 0,
            "peers": 5581,
            "date": "31/12/24 13:12",
            "uploader": "yerisan710:_trusted_uploader::_sitefriend:",
            "S/L": "[185/236]"
        },
        {
            "title": "Wicked.2024.1080p.WEB-DL.H.264.Dual.YG⭐",
            "category": "Movies : HD",
            "language": "Spanish",
            "size": "5.13 GB",
            "seeds": 0,
            "peers": 3355,
            "date": "31/12/24 13:12",
            "uploader": "yerisan710:_trusted_uploader::_sitefriend:",
            "S/L": "[54/212]"
        },
        {
            "title": "Wicked.2024.2160p.WEB-DL.DDP5.1.Atmos.DV.HDR.H.265-FLUX",
            "category": "Movies : 4K UHD",
            "language": "English",
            "size": "28.54 GB",
            "seeds": 9,
            "peers": 23364,
            "date": "31/12/24 08:33",
            "uploader": "JackONeill:_verified_uploader:",
            "S/L": "[371/304]"
        },
        {
            "title": "Wicked.2024.1080p.AMZN.WEB-DL.DUAL.DDP5.1.H.264-KyoGo.mkv",
            "category": "Movies : HD",
            "language": "English",
            "size": "12.10 GB",
            "seeds": 28,
            "peers": 193474,
            "date": "31/12/24 06:11",
            "uploader": "platypusp:_trusted_uploader:",
            "S/L": "[236/50]"
        },
        {
            "title": "Wicked.2024.1080p.WEBRip.10Bit.DDP5.1.x265-Asiimov",
            "category": "Movies : HD",
            "language": "English",
            "size": "2.52 GB",
            "seeds": 12,
            "peers": 45545,
            "date": "31/12/24 04:19",
            "uploader": "Nick007:_trusted_uploader:",
            "S/L": "[5,016/1,943]"
        },
        {
            "title": "Wicked: Part 1 (2024) 1080p CAMRip V2 Hindi HQ Dubbed x264 - 1XBET",
            "category": "Movies : CAM/TS",
            "language": "Hindi",
            "size": "3.99 GB",
            "seeds": 0,
            "peers": 3312,
            "date": "27/11/24 11:13",
            "uploader": "1XCinema:_trusted_uploader:",
            "S/L": "[13/93]"
        },
        {
            "title": "Wicked.2024.1080p.TELESYNC.x264.AC3-AOC",
            "category": "Movies : CAM/TS",
            "language": "English",
            "size": "3.67 GB",
            "seeds": 3,
            "peers": 10596,
            "date": "25/11/24 10:01",
            "uploader": "atomicfusion:_trusted_uploader:",
            "S/L": "[144/82]"
        },
        {
            "title": "Wicked.2024.1080p.TELESYNC.LTE.Version.x264.COLLECTiVE",
            "category": "Movies : CAM/TS",
            "language": "English",
            "size": "4.10 GB",
            "seeds": 12,
            "peers": 18064,
            "date": "24/11/24 20:30",
            "uploader": "will1869:_trusted_uploader::_sitefriend:",
            "S/L": "[600/349]"
        },
        {
            "title": "Wicked.2024.1080p.TELESYNC.x264.COLLECTiVE",
            "category": "Movies : CAM/TS",
            "language": "English",
            "size": "18.79 GB",
            "seeds": 3,
            "peers": 6257,
            "date": "24/11/24 20:26",
            "uploader": "will1869:_trusted_uploader::_sitefriend:",
            "S/L": "[44/33]"
        },
        {
            "title": "Wicked (2024) 1080p CAMRip English x264 - 1XBET",
            "category": "Movies : CAM/TS",
            "language": "English",
            "size": "3.99 GB",
            "seeds": 1,
            "peers": 3729,
            "date": "23/11/24 08:50",
            "uploader": "1XCinema:_trusted_uploader:",
            "S/L": "[17/28]"
        },
        {
            "title": "Wicked.Part.I.2024.HDCAM.c1nem4.x264-SUNSCREEN[TGx]",
            "category": "Movies : CAM/TS",
            "language": "English",
            "size": "996.37 MB",
            "seeds": 28,
            "peers": 75067,
            "date": "23/11/24 05:26",
            "uploader": "TGxMovies:_trusted_uploader:",
            "S/L": "[248/313]"
        },
        {
            "title": "Wicked.Part.I.2024.720p.HDCAM-C1NEM4",
            "category": "Movies : CAM/TS",
            "language": "English",
            "size": "2.21 GB",
            "seeds": 1,
            "peers": 3421,
            "date": "23/11/24 04:34",
            "uploader": "TGxMovies:_trusted_uploader:",
            "S/L": "[50/51]"
        }
    ]
    ```

    This JSON representation includes all the specified fields along with the additional fields like `uploader` and `S/L`.
    """


    print(extract_json_from_string(raw))