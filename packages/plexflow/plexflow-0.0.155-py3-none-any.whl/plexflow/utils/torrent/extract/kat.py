from bs4 import BeautifulSoup
from dateutil.parser import parse

def extract_torrent_results(html):
    """
    Extracts torrent results from HTML content, converting age to absolute date using dateutil.parser.

    Args:
        html: The HTML content as a string.

    Returns:
        A list of dictionaries, each representing a torrent result with keys:
            - 'download_name': The name of the torrent.
            - 'magnet_link': The magnet link for the torrent.
            - 'size': The size of the torrent.
            - 'uploader': The uploader of the torrent.
            - 'age': The absolute date the torrent was uploaded (datetime object).
            - 'seeders': The number of seeders for the torrent.
            - 'leechers': The number of leechers for the torrent.
    """

    soup = BeautifulSoup(html, 'html.parser')
    torrent_results = []

    # Find all table rows that contain torrent data
    torrent_rows = soup.find_all('tr', class_=['odd', 'even'])

    for row in torrent_rows:
        torrent_result = {}

        # Extract download name and link
        download_name_element = row.find('div', class_='torrentname').find('a', class_='cellMainLink')
        if download_name_element:
            torrent_result['download_name'] = download_name_element.text.strip()
            torrent_result['magnet_link'] = download_name_element['href']

        # Extract other data from table cells
        cols = row.find_all('td')
        if len(cols) >= 6:
            torrent_result['size'] = cols[1].text.strip()
            torrent_result['uploader'] = cols[2].text.strip()

            # Extract age and convert to absolute date using dateutil.parser
            age_text = cols[3].text.strip()
            torrent_result["age_text"] = age_text
            if age_text:
                try:
                    torrent_result['age'] = parse(age_text).replace(tzinfo=None)  # Remove timezone info
                except ValueError:
                    torrent_result['age'] = None  # Handle cases where the age format is invalid

            torrent_result['seeders'] = cols[4].text.strip()
            torrent_result['leechers'] = cols[5].text.strip()

        torrent_results.append(torrent_result)

    return torrent_results

# Example usage
html_content = """

<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" dir="auto">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta http-equiv="Content-Style-Type" content="text/css" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Download planet of the apes 2024 Torrents - Kickass Torrents</title>
<meta name="description" content="Come and download planet of the apes 2024 absolutely for free. Fast downloads.">
<link rel="stylesheet" type="text/css" href="/static/all-5.css" charset="utf-8"/>
<link rel="shortcut icon" href="/favicon.ico" />
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png?v=3" />
<!--[if IE 7]>
    <link href="/static/css/ie7.css" rel="stylesheet" type="text/css" />
<![endif]-->
<!--[if IE 8]>
    <link href="/static/css/ie8.css" rel="stylesheet" type="text/css" />
<![endif]-->
<!--[if lt IE 9]>
    
<![endif]-->
<!--[if gte IE 9]>
    <link href="/static/css/ie9.css" rel="stylesheet" type="text/css" />
<![endif]-->

<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"
/>

<style>
    .feedbackButton,.spareBlock{display:none} header a#logo{background: url(/static/images/logo.png?v=3)}
</style>

</head>

<body class="mainBody">
    <div id="wrapper">
        <div id="wrapperInner">
            
                <header>
    <nav id="menu">
        <a href="/" title="kickass" id="logo">
        </a>
        <a href="#" id="showHideSearch">
            <i class="ka ka-zoom">
            </i>
        </a>
        <div id="torrentSearch">
            <form action="/search.php" method="get" id="searchform" accept-charset="utf-8"
            onsubmit="return doSearch(this.q.value);">
                <input id="contentSearch" class="input-big" type="text" name="q" value="planet of the apes 2024"
                autocomplete="off" placeholder="Search query" />
                <div id="searchTool">
                    <button title="search" type="submit" value onfocus="this.blur();" onclick="this.blur();">
                        <i class="ka ka-search">
                        </i>
                    </button>
                </div>
            </form>
        </div>
        <ul id="navigation">
            <li>
                <a href="/browse/">
                    <i class="ka ka-torrent">
                    </i>
                    <span class="menuItem">
                        browse
                    </span>
                </a>
                <ul class="dropdown dp-middle dropdown-msg upper">
                    <li class="topMsg">
                        <a href="/new/">
                            <i class="ka ka16 ka-torrent">
                            </i>
                            latest
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/movies/">
                            <i class="ka ka16 ka-movie lower">
                            </i>
                            Movies
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/tv/">
                            <i class="ka ka16 ka-movie lower">
                            </i>
                            TV
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/music/">
                            <i class="ka ka16 ka-music-note lower">
                            </i>
                            Music
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/games/">
                            <i class="ka ka16 ka-settings lower">
                            </i>
                            Games
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/documentaries/">
                            <i class="ka ka16 ka-bookmark">
                            </i>
                            Doc
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/apps/">
                            <i class="ka ka16 ka-settings lower">
                            </i>
                            Apps
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/anime/">
                            <i class="ka ka16 ka-movie lower">
                            </i>
                            Anime
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/other/">
                            <i class="ka ka16 ka-torrent">
                            </i>
                            Other
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/xxx/">
                            <i class="ka ka16 ka-delete">
                            </i>
                            XXX
                        </a>
                    </li>
                </ul>
            </li>
            <li>
                <a data-nop href="#"> <i class="ka ka-community"></i><span class="menuItem">POPULAR</span></a>
                <ul class="dropdown dp-middle dropdown-msg upper">
                    <li class="topMsg">
                        <a href="/popular">
                            <i class="ka ka16 ka-torrent">
                            </i>
                            all
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/popular-movies">
                            <i class="ka ka16 ka-movie lower">
                            </i>
                            Movies
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/popular-tv">
                            <i class="ka ka16 ka-movie lower">
                            </i>
                            TV
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/popular-music">
                            <i class="ka ka16 ka-music-note lower">
                            </i>
                            Music
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/popular-games">
                            <i class="ka ka16 ka-settings lower">
                            </i>
                            Games
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/popular-documentaries">
                            <i class="ka ka16 ka-bookmark">
                            </i>
                            Doc
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/popular-apps">
                            <i class="ka ka16 ka-settings lower">
                            </i>
                            Apps
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/popular-anime">
                            <i class="ka ka16 ka-movie lower">
                            </i>
                            Anime
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/popular-other">
                            <i class="ka ka16 ka-torrent">
                            </i>
                            Other
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/popular-xxx">
                            <i class="ka ka16 ka-delete">
                            </i>
                            XXX
                        </a>
                    </li>
                </ul>
            </li>
            <li>
                <a data-nop href="#"><i class="ka ka-rss lower"></i><span class="menuItem">TOP</span></a>
                <ul class="dropdown dp-middle dropdown-msg upper">
                    <li class="topMsg">
                        <a href="/top-100">
                            <i class="ka ka16 ka-torrent">
                            </i>
                            all
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/top-100-movies">
                            <i class="ka ka16 ka-movie lower">
                            </i>
                            Movies
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/top-100-television">
                            <i class="ka ka16 ka-movie lower">
                            </i>
                            TV
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/top-100-music">
                            <i class="ka ka16 ka-music-note lower">
                            </i>
                            Music
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/top-100-games">
                            <i class="ka ka16 ka-settings lower">
                            </i>
                            Games
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/top-100-documentaries">
                            <i class="ka ka16 ka-bookmark">
                            </i>
                            Doc
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/top-100-applications">
                            <i class="ka ka16 ka-settings lower">
                            </i>
                            Apps
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/top-100-anime">
                            <i class="ka ka16 ka-movie lower">
                            </i>
                            Anime
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/top-100-other">
                            <i class="ka ka16 ka-torrent">
                            </i>
                            Other
                        </a>
                    </li>
                    <li class="topMsg">
                        <a href="/top-100-xxx">
                            <i class="ka ka16 ka-delete">
                            </i>
                            XXX
                        </a>
                    </li>
                </ul>
            </li>
            <li><a data-nop href="/register/" class="ajaxLink1"><i class="ka ka-user"></i><span class="menuItem">Register</span></a></li>
        </ul>
    </nav>
</header>
<div class="pusher">
</div>
            
            
    <div class="mainpart">
        <table width="100%" cellspacing="0" cellpadding="0" class="doublecelltable">
            <tbody>
                <tr>
                    <td width="100%">
                        <div class="tabs">
                            <ul class="tabNavigation">
                                <li>
                                    <a class="darkButton " href="/search/planet of the apes 2024/">
                                        <span>
                                            All
                                        </span>
                                    </a>
                                </li>
                                <li>
                                        <a rel="nofollow" class="darkButton selectedTab" href="/search/planet of the apes 2024/category/movies/">
                                            <span>
                                                Movies                                            </span>
                                        </a>
                                    </li><li>
                                        <a rel="nofollow" class="darkButton " href="/search/planet of the apes 2024/category/tv/">
                                            <span>
                                                TV                                            </span>
                                        </a>
                                    </li><li>
                                        <a rel="nofollow" class="darkButton " href="/search/planet of the apes 2024/category/music/">
                                            <span>
                                                Music                                            </span>
                                        </a>
                                    </li><li>
                                        <a rel="nofollow" class="darkButton " href="/search/planet of the apes 2024/category/games/">
                                            <span>
                                                Games                                            </span>
                                        </a>
                                    </li><li>
                                        <a rel="nofollow" class="darkButton " href="/search/planet of the apes 2024/category/documentaries/">
                                            <span>
                                                Documentaries                                            </span>
                                        </a>
                                    </li><li>
                                        <a rel="nofollow" class="darkButton " href="/search/planet of the apes 2024/category/apps/">
                                            <span>
                                                Apps                                            </span>
                                        </a>
                                    </li><li>
                                        <a rel="nofollow" class="darkButton " href="/search/planet of the apes 2024/category/anime/">
                                            <span>
                                                Anime                                            </span>
                                        </a>
                                    </li><li>
                                        <a rel="nofollow" class="darkButton " href="/search/planet of the apes 2024/category/other/">
                                            <span>
                                                Other                                            </span>
                                        </a>
                                    </li><li>
                                        <a rel="nofollow" class="darkButton " href="/search/planet of the apes 2024/category/xxx/">
                                            <span>
                                                XXX                                            </span>
                                        </a>
                                    </li>                            </ul>
                            <hr class="tabsSeparator">
                        </div>
                        <nav class="searchTags">
                                <ul>
                                    <li>
                                        <a href="/search/planet of the apes 2024/">
                                            in movies                                        </a>
                                    </li>
                                </ul>
                            </nav>                        <table width="100%" cellspacing="0" cellpadding="0" class="doublecelltable">
                            <tbody>
                                <tr>
                                    <td width="100%">
                                        <h2>
                                            <a class="plain" href="javascript:void(0)">
                                                planet of the apes 2024 results 1-20 from 48                                            </a>
                                        </h2>
                                        <div>
                                            <table cellpadding="0" cellspacing="0" class="data frontPageWidget" style="width: 100%">
    <tbody>
        <tr class="firstr">
            <th class="width100perc nopad">torrent name</th>
            <th class="center">
                                <a href="?sortby=size&sort=desc">size</a>            </th>
            <th class="center">
                    uploader
            </th>
            <th class="center">
                <a href="?sortby=time&sort=asc" style="padding: 0 2.9em;">age</a>
                            </th>
            <th class="center">
                                <a href="?sortby=seeders&sort=desc">seed</a>            </th>
            <th class="lasttd nobr center">
                                <a href="?sortby=leechers&sort=desc">leech</a>            </th>
        </tr>
        <tr class="odd" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-1080p-10bit-webrip-hindi-ddp-5-1-english-aac-5-1-dual-audio-x265-hevc-esubs-psa-protonmovies-t6181666.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-10bit-webrip-hindi-ddp-5-1-english-aac-5-1-dual-audio-x265-hevc-esubs-psa-t6181666.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-10bit-webrip-hindi-ddp-5-1-english-aac-5-1-dual-audio-x265-hevc-esubs-psa-t6181666.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-10bit-webrip-hindi-ddp-5-1-english-aac-5-1-dual-audio-x265-hevc-esubs-psa-t6181666.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">The</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">The</strong> <strong class="red">Apes</strong> (<strong class="red">2024</strong>) 1080p 10bit WEBRip  Hindi DDP 5 1 + English AAC 5 1  Dual Audio x265 HEVC ESubs - PSA  ProtonMovies                             </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/AlejandroAXL/">
                                    AlejandroAXL                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/dubs+dual-audio/">
                                            Dubs/Dual Audio                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    2.5 GB                </td>
                <td class="center">
                    AlejandroAXL                </td>
                <td class="center" title="4<br/>days">
                    4<br/>days                </td>
                <td class="green center">
                    64                </td>
                <td class="red lasttd center">
                    55                </td>
            </tr><tr class="even" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-720p-10bit-webrip-hindi-ddp-5-1-english-aac5-1-dual-audio-x265-hevc-esubs-psa-protonmovies-t6181668.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-10bit-webrip-hindi-ddp-5-1-english-aac5-1-dual-audio-x265-hevc-esubs-psa-protonmovies-t6181668.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-10bit-webrip-hindi-ddp-5-1-english-aac5-1-dual-audio-x265-hevc-esubs-psa-protonmovies-t6181668.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-10bit-webrip-hindi-ddp-5-1-english-aac5-1-dual-audio-x265-hevc-esubs-psa-protonmovies-t6181668.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">The</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">The</strong> <strong class="red">Apes</strong> (<strong class="red">2024</strong>) 720p 10bit WEBRip  Hindi DDP 5 1 + English AAC5 1  Dual Audio x265 HEVC ESubs - PSA  ProtonMovies                             </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/AlejandroAXL/">
                                    AlejandroAXL                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/dubs+dual-audio/">
                                            Dubs/Dual Audio                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    1.4 GB                </td>
                <td class="center">
                    AlejandroAXL                </td>
                <td class="center" title="4<br/>days">
                    4<br/>days                </td>
                <td class="green center">
                    40                </td>
                <td class="red lasttd center">
                    30                </td>
            </tr><tr class="odd" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-720p-webrip-hindi-english-x264-aac-gopihd-t6179756.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-webrip-hindi-english-x264-aac-gopihd-t6179756.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-webrip-hindi-english-x264-aac-gopihd-t6179756.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-webrip-hindi-english-x264-aac-gopihd-t6179756.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">Of</strong> <strong class="red">The</strong> <strong class="red">Planet</strong> <strong class="red">Of</strong> <strong class="red">The</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> 720p WEBRip HINDI ENGLISH  x264 AAC-GOPIHD                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/MrX123/">
                                    MrX123                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/dubs+dual-audio/">
                                            Dubs/Dual Audio                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    1.5 GB                </td>
                <td class="center">
                    MrX123                </td>
                <td class="center" title="7<br/>days">
                    7<br/>days                </td>
                <td class="green center">
                    27                </td>
                <td class="red lasttd center">
                    11                </td>
            </tr><tr class="even" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-1080p-webrip-hindi-english-aac-10bit-x265-gopihd-t6179754.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-webrip-hindi-english-aac-10bit-x265-gopihd-t6179754.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-webrip-hindi-english-aac-10bit-x265-gopihd-t6179754.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-webrip-hindi-english-aac-10bit-x265-gopihd-t6179754.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">Of</strong> <strong class="red">The</strong> <strong class="red">Planet</strong> <strong class="red">Of</strong> <strong class="red">The</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> 1080p WEBRip HINDI ENGLISH AAC 10BIT X265-GOPIHD                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/MrX123/">
                                    MrX123                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/dubs+dual-audio/">
                                            Dubs/Dual Audio                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    1.8 GB                </td>
                <td class="center">
                    MrX123                </td>
                <td class="center" title="7<br/>days">
                    7<br/>days                </td>
                <td class="green center">
                    77                </td>
                <td class="red lasttd center">
                    26                </td>
            </tr><tr class="odd" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-720p-webrip-x265-aac-hin-eng-esub-t6179703.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-webrip-x265-aac-hin-eng-esub-t6179703.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-webrip-x265-aac-hin-eng-esub-t6179703.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-webrip-x265-aac-hin-eng-esub-t6179703.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">Of</strong> <strong class="red">The</strong> <strong class="red">Planet</strong> <strong class="red">Of</strong> <strong class="red">The</strong> <strong class="red">Apes</strong> (<strong class="red">2024</strong>) 720p WEBRip  x265  AAC   Hin, Eng   ESub                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/krishh1337/">
                                    krishh1337                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/dubs+dual-audio/">
                                            Dubs/Dual Audio                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    1 GB                </td>
                <td class="center">
                    krishh1337                </td>
                <td class="center" title="7<br/>days">
                    7<br/>days                </td>
                <td class="green center">
                    107                </td>
                <td class="red lasttd center">
                    74                </td>
            </tr><tr class="even" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-1080p-amzn-web-dl-x265-hevc-10bit-eac3-5-1-silence-qxr-t6161691.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-amzn-web-dl-x265-hevc-10bit-eac3-5-1-silence-qxr-t6161691.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-amzn-web-dl-x265-hevc-10bit-eac3-5-1-silence-qxr-t6161691.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-amzn-web-dl-x265-hevc-10bit-eac3-5-1-silence-qxr-t6161691.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> (<strong class="red">2024</strong>) (1080p AMZN WEB-DL x265 HEVC 10bit EAC3 5 1 Silence)  QxR                             </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/QxR/">
                                    QxR                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hevc+x265/">
                                            HEVC/x265                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    6.4 GB                </td>
                <td class="center">
                    QxR                </td>
                <td class="center" title="27<br/>days">
                    27<br/>days                </td>
                <td class="green center">
                    230                </td>
                <td class="red lasttd center">
                    101                </td>
            </tr><tr class="odd" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-1080p-web-rip-ds4k-10bit-hevc-ddp5-1-atmos-esub-nmct-t6161440.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-web-rip-ds4k-10bit-hevc-ddp5-1-atmos-esub-nmct-t6161440.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-web-rip-ds4k-10bit-hevc-ddp5-1-atmos-esub-nmct-t6161440.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-web-rip-ds4k-10bit-hevc-ddp5-1-atmos-esub-nmct-t6161440.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">The</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">The</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> 1080p WEB-Rip DS4K 10bit HEVC DDP5 1 Atmos ESub-NmCT                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/WiCK0028/">
                                    WiCK0028                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hevc+x265/">
                                            HEVC/x265                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    5.7 GB                </td>
                <td class="center">
                    WiCK0028                </td>
                <td class="center" title="28<br/>days">
                    28<br/>days                </td>
                <td class="green center">
                    46                </td>
                <td class="red lasttd center">
                    36                </td>
            </tr><tr class="even" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-2160p-hdr10plus-dv-webrip-6ch-x265-hevc-psa-t6161420.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-2160p-hdr10plus-dv-webrip-6ch-x265-hevc-psa-t6161420.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-2160p-hdr10plus-dv-webrip-6ch-x265-hevc-psa-t6161420.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-2160p-hdr10plus-dv-webrip-6ch-x265-hevc-psa-t6161420.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> 2160p HDR10Plus DV WEBRip 6CH x265 HEVC-PSA                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/mazemaze16/">
                                    mazemaze16                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hevc+x265/">
                                            HEVC/x265                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    4.5 GB                </td>
                <td class="center">
                    mazemaze16                </td>
                <td class="center" title="28<br/>days">
                    28<br/>days                </td>
                <td class="green center">
                    49                </td>
                <td class="red lasttd center">
                    66                </td>
            </tr><tr class="odd" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-1080p-webrip-x265-kontrast-t6160656.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-webrip-x265-kontrast-t6160656.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-webrip-x265-kontrast-t6160656.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-webrip-x265-kontrast-t6160656.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> 1080p WEBRip x265-KONTRAST                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/rondobym/">
                                    rondobym                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hevc+x265/">
                                            HEVC/x265                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    2.7 GB                </td>
                <td class="center">
                    rondobym                </td>
                <td class="center" title="28<br/>days">
                    28<br/>days                </td>
                <td class="green center">
                    60                </td>
                <td class="red lasttd center">
                    66                </td>
            </tr><tr class="even" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-720p-webrip-x265-proton-t6160657.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-webrip-x265-proton-t6160657.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-webrip-x265-proton-t6160657.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-720p-webrip-x265-proton-t6160657.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> 720p WEBRip x265-PROTON                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/rondobym/">
                                    rondobym                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hevc+x265/">
                                            HEVC/x265                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    1.4 GB                </td>
                <td class="center">
                    rondobym                </td>
                <td class="center" title="28<br/>days">
                    28<br/>days                </td>
                <td class="green center">
                    25                </td>
                <td class="red lasttd center">
                    24                </td>
            </tr><tr class="odd" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-il-regno-del-pianeta-delle-scimmie-2024-ita-eng-ac3-5-1-sub-ita-webrip-1080p-h264-armor-t6160503.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-il-regno-del-pianeta-delle-scimmie-2024-ita-eng-ac3-5-1-sub-ita-webrip-1080p-h264-armor-t6160503.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-il-regno-del-pianeta-delle-scimmie-2024-ita-eng-ac3-5-1-sub-ita-webrip-1080p-h264-armor-t6160503.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-il-regno-del-pianeta-delle-scimmie-2024-ita-eng-ac3-5-1-sub-ita-webrip-1080p-h264-armor-t6160503.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> - Il Regno del Pianeta delle Scimmie (<strong class="red">2024</strong>) ITA ENG Ac3 5 1 sub Ita WEBRip 1080p H264  ArMor                             </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/ArMor/">
                                    ArMor                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hd/">
                                            HD                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    3.6 GB                </td>
                <td class="center">
                    ArMor                </td>
                <td class="center" title="28<br/>days">
                    28<br/>days                </td>
                <td class="green center">
                    27                </td>
                <td class="red lasttd center">
                    16                </td>
            </tr><tr class="even" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-2160p-amzn-web-dl-ddp5-1-atmos-h-265-xebec-t6160327.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-2160p-amzn-web-dl-ddp5-1-atmos-h-265-xebec-t6160327.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-2160p-amzn-web-dl-ddp5-1-atmos-h-265-xebec-t6160327.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-2160p-amzn-web-dl-ddp5-1-atmos-h-265-xebec-t6160327.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> 2160p AMZN WEB-DL DDP5 1 Atmos H 265-XEBEC                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/mazemaze16/">
                                    mazemaze16                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hevc+x265/">
                                            HEVC/x265                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    15.7 GB                </td>
                <td class="center">
                    mazemaze16                </td>
                <td class="center" title="29<br/>days">
                    29<br/>days                </td>
                <td class="green center">
                    121                </td>
                <td class="red lasttd center">
                    93                </td>
            </tr><tr class="odd" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-1080p-amzn-web-dl-ddp5-1-h-264-xebec-t6160323.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-amzn-web-dl-ddp5-1-h-264-xebec-t6160323.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-amzn-web-dl-ddp5-1-h-264-xebec-t6160323.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-amzn-web-dl-ddp5-1-h-264-xebec-t6160323.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> 1080p AMZN WEB-DL DDP5 1 H 264-XEBEC                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/mazemaze16/">
                                    mazemaze16                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/h.264+x264/">
                                            h.264/x264                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    8.3 GB                </td>
                <td class="center">
                    mazemaze16                </td>
                <td class="center" title="29<br/>days">
                    29<br/>days                </td>
                <td class="green center">
                    244                </td>
                <td class="red lasttd center">
                    88                </td>
            </tr><tr class="even" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-spanish-latino-1080p-web-dl-ddp7-1-h-264-dem3nt3-t6160011.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-spanish-latino-1080p-web-dl-ddp7-1-h-264-dem3nt3-t6160011.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-spanish-latino-1080p-web-dl-ddp7-1-h-264-dem3nt3-t6160011.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-spanish-latino-1080p-web-dl-ddp7-1-h-264-dem3nt3-t6160011.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> SPANiSH LATiNO 1080p WEB-DL DDP7 1 H 264-dem3nt3                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/outr0x/">
                                    outr0x                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hd/">
                                            HD                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    8.7 GB                </td>
                <td class="center">
                    outr0x                </td>
                <td class="center" title="29<br/>days">
                    29<br/>days                </td>
                <td class="green center">
                    14                </td>
                <td class="red lasttd center">
                    34                </td>
            </tr><tr class="odd" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-spanish-latino-2160p-web-dl-ddp7-1-hdr10-h-265-dem3nt3-t6160012.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-spanish-latino-2160p-web-dl-ddp7-1-hdr10-h-265-dem3nt3-t6160012.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-spanish-latino-2160p-web-dl-ddp7-1-hdr10-h-265-dem3nt3-t6160012.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-spanish-latino-2160p-web-dl-ddp7-1-hdr10-h-265-dem3nt3-t6160012.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> SPANiSH LATiNO 2160p WEB-DL DDP7 1 HDR10 H 265-dem3nt3                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/outr0x/">
                                    outr0x                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hevc+x265/">
                                            HEVC/x265                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    26.3 GB                </td>
                <td class="center">
                    outr0x                </td>
                <td class="center" title="29<br/>days">
                    29<br/>days                </td>
                <td class="green center">
                    21                </td>
                <td class="red lasttd center">
                    75                </td>
            </tr><tr class="even" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#planet-of-the-apes-il-pianeta-delle-scimmie-saga-2011-2024-1080p-h265-ac3-5-1-ita-eng-sub-ita-eng-mircrew-t6159912.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/planet-of-the-apes-il-pianeta-delle-scimmie-saga-2011-2024-1080p-h265-ac3-5-1-ita-eng-sub-ita-eng-mircrew-t6159912.html"
                        class="torType filmType">
                        </a>
                        <a href="/planet-of-the-apes-il-pianeta-delle-scimmie-saga-2011-2024-1080p-h265-ac3-5-1-ita-eng-sub-ita-eng-mircrew-t6159912.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/planet-of-the-apes-il-pianeta-delle-scimmie-saga-2011-2024-1080p-h265-ac3-5-1-ita-eng-sub-ita-eng-mircrew-t6159912.html"
                            class="cellMainLink">
                                <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> - Il pianeta delle scimmie Saga (2011-<strong class="red">2024</strong>) 1080p H265 AC3 5 1 ITA ENG sub ita eng MIRCrew                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/robbyrs/">
                                    robbyrs                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hevc+x265/">
                                            HEVC/x265                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    12.6 GB                </td>
                <td class="center">
                    robbyrs                </td>
                <td class="center" title="29<br/>days">
                    29<br/>days                </td>
                <td class="green center">
                    5                </td>
                <td class="red lasttd center">
                    12                </td>
            </tr><tr class="odd" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#planet-of-the-apes-il-pianeta-delle-scimmie-saga-2011-2024-2160p-h265-hdr10-ac3-5-1-ita-eng-sub-ita-eng-mircrew-t6159913.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/planet-of-the-apes-il-pianeta-delle-scimmie-saga-2011-2024-2160p-h265-hdr10-ac3-5-1-ita-eng-sub-ita-eng-mircrew-t6159913.html"
                        class="torType filmType">
                        </a>
                        <a href="/planet-of-the-apes-il-pianeta-delle-scimmie-saga-2011-2024-2160p-h265-hdr10-ac3-5-1-ita-eng-sub-ita-eng-mircrew-t6159913.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/planet-of-the-apes-il-pianeta-delle-scimmie-saga-2011-2024-2160p-h265-hdr10-ac3-5-1-ita-eng-sub-ita-eng-mircrew-t6159913.html"
                            class="cellMainLink">
                                <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> - Il pianeta delle scimmie Saga (2011-<strong class="red">2024</strong>) 2160p H265 HDR10 AC3 5 1 ITA ENG sub ita eng MIRCrew                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/robbyrs/">
                                    robbyrs                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hevc+x265/">
                                            HEVC/x265                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    16.1 GB                </td>
                <td class="center">
                    robbyrs                </td>
                <td class="center" title="29<br/>days">
                    29<br/>days                </td>
                <td class="green center">
                    7                </td>
                <td class="red lasttd center">
                    6                </td>
            </tr><tr class="even" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#kingdom-of-the-planet-of-the-apes-2024-4k-hdr-dv-2160p-webdl-ita-eng-x265-nahom-t6159794.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-4k-hdr-dv-2160p-webdl-ita-eng-x265-nahom-t6159794.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-4k-hdr-dv-2160p-webdl-ita-eng-x265-nahom-t6159794.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-4k-hdr-dv-2160p-webdl-ita-eng-x265-nahom-t6159794.html"
                            class="cellMainLink">
                                Kingdom <strong class="red">Of</strong> <strong class="red">The</strong> <strong class="red">Planet</strong> <strong class="red">Of</strong> <strong class="red">The</strong> <strong class="red">Apes</strong> <strong class="red">2024</strong> 4K HDR DV 2160p WEBDL Ita Eng x265-NAHOM                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/NAHOM1/">
                                    NAHOM1                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/uhd/">
                                            UHD                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    25.6 GB                </td>
                <td class="center">
                    NAHOM1                </td>
                <td class="center" title="29<br/>days">
                    29<br/>days                </td>
                <td class="green center">
                    46                </td>
                <td class="red lasttd center">
                    74                </td>
            </tr><tr class="odd" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-1080p-h265-webdl-rip-ita-eng-ac3-5-1-sub-ita-eng-licdom-t6159679.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-10bit-webrip-hindi-ddp-5-1-english-aac-5-1-dual-audio-x265-hevc-esubs-psa-il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-1080p-h265-webdl-rip-ita-eng-ac3-5-1-sub-ita-t6159679.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-10bit-webrip-hindi-ddp-5-1-english-aac-5-1-dual-audio-x265-hevc-esubs-psa-il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-1080p-h265-webdl-rip-ita-eng-ac3-5-1-sub-ita-t6159679.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-10bit-webrip-hindi-ddp-5-1-english-aac-5-1-dual-audio-x265-hevc-esubs-psa-il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-1080p-h265-webdl-rip-ita-eng-ac3-5-1-sub-ita-t6159679.html"
                            class="cellMainLink">
                                Il regno del pianeta delle scimmie - Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> (<strong class="red">2024</strong>) 1080p H265 WebDl Rip ita eng AC3 5 1 sub ita eng Licdom                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/licdom/">
                                    licdom                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/hd/">
                                            HD                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    3.3 GB                </td>
                <td class="center">
                    licdom                </td>
                <td class="center" title="29<br/>days">
                    29<br/>days                </td>
                <td class="green center">
                    32                </td>
                <td class="red lasttd center">
                    7                </td>
            </tr><tr class="even" >
                <td>
                    <div class="iaconbox center floatright">
                        <a data-download="" title="Download torrent file" target="_blank" href="#il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-2160p-h265-webdl-rip-10-bit-dv-hdr10-ita-eng-ac3-5-1-sub-ita-eng-licdom-t6159680.html"
                        class="icon16">
                            <i class="ka ka16 ka-arrow-down">
                            </i>
                        </a>
                    </div>
                    <div class="torrentname">
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-10bit-webrip-hindi-ddp-5-1-english-aac-5-1-dual-audio-x265-hevc-esubs-psa-il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-1080p-h265-webdl-rip-ita-eng-ac3-5-1-sub-ita-il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-2160p-h265-webdl-rip-10-bit-dv-hdr10-ita-eng-ac3-t6159680.html"
                        class="torType filmType">
                        </a>
                        <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-10bit-webrip-hindi-ddp-5-1-english-aac-5-1-dual-audio-x265-hevc-esubs-psa-il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-1080p-h265-webdl-rip-ita-eng-ac3-5-1-sub-ita-il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-2160p-h265-webdl-rip-10-bit-dv-hdr10-ita-eng-ac3-t6159680.html"
                        class="normalgrey font12px plain bold">
                        </a>
                        <div class="markeredBlock torType filmType">
                            <a href="/kingdom-of-the-planet-of-the-apes-2024-1080p-10bit-webrip-hindi-ddp-5-1-english-aac-5-1-dual-audio-x265-hevc-esubs-psa-il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-1080p-h265-webdl-rip-ita-eng-ac3-5-1-sub-ita-il-regno-del-pianeta-delle-scimmie-kingdom-of-the-planet-of-the-apes-2024-2160p-h265-webdl-rip-10-bit-dv-hdr10-ita-eng-ac3-t6159680.html"
                            class="cellMainLink">
                                Il regno del pianeta delle scimmie - Kingdom <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Planet</strong> <strong class="red">of</strong> <strong class="red">the</strong> <strong class="red">Apes</strong> (<strong class="red">2024</strong>) 2160p H265 WebDl Rip 10 bit DV HDR10+ ita eng AC3 5 1 sub ita eng Licdom                            </a>
                            <span class="font11px lightgrey block">
                                Posted by
                                <i title="Verified Uploader" class="ka ka-verify" style="font-size: 16px;color:orange;">
                                </i>
                                <a class="plain" href="/user/licdom/">
                                    licdom                                </a>
                                in
                                <span>
                                    <strong>
                                        <a href="/movies/">
                                            Movies                                        </a> &gt; 
                                        <a href="/movies/uhd/">
                                            UHD                                        </a>
                                    </strong>
                                </span>
                            </span>
                        </div>
                    </div>
                </td>
                <td class="nobr center">
                    5.5 GB                </td>
                <td class="center">
                    licdom                </td>
                <td class="center" title="29<br/>days">
                    29<br/>days                </td>
                <td class="green center">
                    27                </td>
                <td class="red lasttd center">
                    18                </td>
            </tr>    </tbody>
</table>
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                        <div class="pages botmarg5px floatright">  <a href="javascript:void(0)" class="turnoverButton siteButton bigButton active">1</a><a class="turnoverButton siteButton bigButton" href="/search/planet%20of%20the%20apes%202024/category/movies/2/">2</a><a class="turnoverButton siteButton bigButton" href="/search/planet%20of%20the%20apes%202024/category/movies/3/">3</a> <a class="turnoverButton siteButton bigButton" href="/search/planet%20of%20the%20apes%202024/category/movies/2/">>></a> </ul></div>                    </td>
                    <td class="sidebarCell">
<div id="sidebar">
    <div class="sliderbox">
        <h3>
            Latest Searches
            <i class="sliderBoxToggle ka ka16 ka-arrow2-up foldClose">
            </i>
        </h3>
        <ul id="latestSearches" rel="latestSearches" class="showBlockJS">
        	        	<li>
				<a href="/search/BOOTY/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">BOOTY</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/The+mermaid/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">The+mermaid</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/True detective/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">True detective</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/babes/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">babes</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/heroes might magic 5/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">heroes might magic 5</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/Jane mcdonald/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">Jane mcdonald</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/mummies 2014/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">mummies 2014</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/aerial america s08e05/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">aerial america s08e05</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/psychology/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">psychology</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/9.0.2704.0/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">9.0.2704.0</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/Whose Line is it Anyway (USA) S01E11/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">Whose Line is it Anyway (USA) S01E11</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li><li>
				<a href="/search/spider man 15/"><i class="ka ka16 ka-zoom latest-icon"></i><p class="latest-title">spider man 15</p></a>
				<span class="explanation">just&nbsp;now</span>
			</li>        </ul>
    </div>
    <div class="sliderbox">
        <h3>
            Friends Links
            <i class="sliderBoxToggle ka ka16 ka-arrow2-up foldClose">
            </i>
        </h3>
        <ul id="friendsLinks" rel="friendsLinks" class="showBlockJS">
        	        	<li>
                <a data-nop="" href="https://1337x.torrentbay.st" target="_blank" rel="external">1337x
</a>
            </li><li>
                <a data-nop="" href="https://thepiratebay.torrentbay.st" target="_blank" rel="external">ThePirateBay
</a>
            </li><li>
                <a data-nop="" href="https://limetorrents.torrentbay.st" target="_blank" rel="external">LimeTorrents
</a>
            </li><li>
                <a data-nop="" href="https://yts.torrentbay.st" target="_blank" rel="external">YTS
</a>
            </li><li>
                 
</a>
            </li><li>
                 
            </li>        </ul>
    </div>
</div>
</td>
                </tr>
            </tbody>
        </table>
    </div>

        </div>
    </div>
    <footer class="lightgrey">
    <ul>
        <li><a href="/dmca/">dmca</a></li>
        <li><a target="_blank" href="https://kickass.torrentbay.st">Kickass Torrents</a></li>
    </ul>
</footer>
 


    
    

     
 

 
 
<script
  src="https://code.jquery.com/jquery-3.5.1.min.js"
  integrity="sha256-9/aliU8dGd2tb6OSsuzixeV4y/faTqgFtohetphbbj0="
  crossorigin="anonymous"></script>
<script>
$(function(){
		if ($('[itemprop="name"]').length) {
		var magnet = $('[title="Magnet link"]').eq(0).attr("href");
	
		$("[data-download]").attr("href", magnet);
		}
	

});
</script><script type="text/javascript" data-cfasync="false">
/*<![CDATA[/* */
(function(){var v=window,a="b39e0a351e068608a4f5b6827ac0a713",u=[["siteId",919-150-853-832+5073105],["minBid",0],["popundersPerIP","0"],["delayBetween",0],["default",false],["defaultPerDay",0],["topmostLayer","auto"]],y=["d3d3LmludGVsbGlwb3B1cC5jb20vSktqL2xtaWRuaWdodC5qcXVlcnkubWluLmpz","ZDNtcjd5MTU0ZDJxZzUuY2xvdWRmcm9udC5uZXQvWFRDTS9yS0htZy9iYm90dWkubWluLmNzcw==","d3d3LnZwa2RyeHl4LmNvbS93bXBLVC92bWlkbmlnaHQuanF1ZXJ5Lm1pbi5qcw==","d3d3LmVvZWRjaHVjZHRrZXAuY29tL21sL0ZGRmwveGJvdHVpLm1pbi5jc3M="],t=-1,j,r,n=function(){clearTimeout(r);t++;if(y[t]&&!(1748944149000<(new Date).getTime()&&1<t)){j=v.document.createElement("script");j.type="text/javascript";j.async=!0;var s=v.document.getElementsByTagName("script")[0];j.src="https://"+atob(y[t]);j.crossOrigin="anonymous";j.onerror=n;j.onload=function(){clearTimeout(r);v[a.slice(0,16)+a.slice(0,16)]||n()};r=setTimeout(n,5E3);s.parentNode.insertBefore(j,s)}};if(!v[a]){try{Object.freeze(v[a]=u)}catch(e){}n()}})();
/*]]>/* */
</script>
<script
  src="https://code.jquery.com/jquery-3.5.1.min.js"
  integrity="sha256-9/aliU8dGd2tb6OSsuzixeV4y/faTqgFtohetphbbj0="
  crossorigin="anonymous"></script>
<script>
$(function(){
		if ($('[itemprop="name"]').length) {
		var magnet = $('[title="Magnet link"]').eq(0).attr("href");
	
		$("[data-download]").attr("href", magnet);
		}
	

});
</script></body>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js"></script><script src="/js/file.js"></script></html>
"""

results = extract_torrent_results(html_content)
print(results)