from bs4 import BeautifulSoup
from plexflow.utils.strings.filesize import parse_size
import dateparser

def extract_torrent_results(html):
    """
    Extracts torrent results from the provided HTML string.

    Args:
        html: The HTML string to parse.

    Returns:
        A list of dictionaries containing torrent information:
            - torrent_name: The name of the torrent.
            - size: The size of the torrent.
            - files: The number of files in the torrent.
            - age: The age of the torrent.
            - seed: The number of seeders.
            - leech: The number of leechers.
            - category: The category of the torrent.
    """

    soup = BeautifulSoup(html, 'html.parser')

    # Find the table containing torrent results
    torrent_table = soup.find('table')

    if not torrent_table:
        return []

    torrents = []

    # Iterate over each torrent row
    for row in torrent_table.find_all('tr'):
        # Extract torrent information from each cell
        cells = row.find_all('td')
        if cells:
            torrent_name = cells[0].find('a').text.strip()
            size = cells[1].text.strip()
            files = cells[2].text.strip()
            age = cells[3].text.strip()
            seed = cells[4].find('span', class_='text-success').text.strip()
            leech = cells[5].find('span', class_='text-danger').text.strip()

            # Find the category in the first cell
            category_span = cells[0].find('span', class_='related-posted')
            category = category_span.find('strong', class_='').find('a').text.strip() if category_span else "Unknown"

            size_bytes = next(iter(parse_size(size)), None)
            date = dateparser.parse(age)
            
            link = "https://ext.to" + cells[0].find('a')['href']  # Extract the 'href' attribute
            
            # Add torrent information to the list
            torrents.append({
                'name': torrent_name,
                'size': size,
                'size_bytes': size_bytes,
                'files': files,
                'age': age,
                'date': date,
                'seeds': seed,
                'peers': leech,
                'type': category,
                'link': link,
            })

    return torrents


if __name__ == "__main__":
    html = r"""
<html lang="en" class="dark-mode"><head>
	<meta content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" name="viewport">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<link rel="apple-touch-icon" href="/static/img/apple-icon.png">
	<link rel="icon" href="/static/img/favicon.png">
	<link rel="stylesheet" type="text/css" href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700%7CRoboto+Slab:400,700%7CMaterial+Icons">
	<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/font-awesome/latest/css/font-awesome.min.css">
		<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="description" content="We have found: 500 'Deadpool 2016' torrents in Movies category, Results Updated: 16 August 2024">
<link href="/static/css/kit.css?1701032447387478" type="text/css" data-template-style="true" rel="stylesheet">
<link href="/static/css/main.css?172158360561985" type="text/css" data-template-style="true" rel="stylesheet">
<link href="/static/css/dark-theme.css?1705274515364294" type="text/css" data-template-style="true" rel="stylesheet">
<link rel="canonical" href="https://ext.to/search/deadpool-2016/">



	<meta name="color-scheme" content="light dark">	
	<title>Download Deadpool 2016 Torrent (500 results) - EXT Torrents</title>	

		
		
	
<link rel="dns-prefetch" href="//jacwkbauzs.com"><link rel="dns-prefetch" href="//youradexchange.com"><link rel="dns-prefetch" href="//kzvcggahkgm.com"></head>
<body>
<header>
	<div class="header-top">
		<div class="container">
			<div class="header-top-left">
				<a href="/" class="logo">
					<img src="/static/img/ext_logo.png" alt="EXT Torrents" title="EXT Torrents">
				</a>
								
				<div class="mobile-profile-block">
											<div class="header-top-right">
							<div class="header-top-right-second">
								<a href="javascript:void(0);" class="header-top-nav" data-toggle="modal" data-target="#loginModal">Log In</a>
								<a href="javascript:void(0);" class="header-top-nav header-top-nav-special" data-toggle="modal" data-target="#registerModal">Sign Up</a>
							</div>
						</div>	
									</div>

				<form action="/search/">
					<div class="form-search-input">
						<span class="bmd-form-group is-filled"><input type="text" name="q" value="Deadpool 2016" autocomplete="off" class="search-input live-search" placeholder="Search for torrents..." required=""></span>
						<div class="livesearch-menu">
							<div class="livesearch-dataset livesearch-dataset-qs">
							</div>
						</div>
					</div>
					<button type="submit"></button>
				</form>
			</div>

			<div class="header-top-right">
				<div class="header-top-right-first">
					<a class="header-top-nav" href="/browse/">Browse</a>
					<a class="header-top-nav" href="/tv-series/">TV Series</a>
				</div>
				<div class="header-top-right-second js-profile-open">
											<a href="javascript:void(0);" class="header-top-nav" data-toggle="modal" data-target="#loginModal">Log In</a>
						<a href="javascript:void(0);" class="header-top-nav header-top-nav-special" data-toggle="modal" data-target="#registerModal">Sign Up</a>
									</div>
			</div>
		</div>
	</div>
		
	<div class="header-bottom">
		<nav class="container">
			
<ul class="header-navigation">
			<li>
			<a href="/latest/" class="">
				All			</a>
		</li>
			<li>
			<a href="/movies/" class="">
				Movies			</a>
		</li>
			<li>
			<a href="/tv/" class="">
				TV			</a>
		</li>
			<li>
			<a href="/music/" class="">
				Music			</a>
		</li>
			<li>
			<a href="/games/" class="">
				Games			</a>
		</li>
			<li>
			<a href="/applications/" class="">
				Apps			</a>
		</li>
			<li>
			<a href="/books/" class="">
				Books			</a>
		</li>
			<li>
			<a href="/anime/" class="">
				Anime			</a>
		</li>
			<li>
			<a href="/xxx/" class="">
				Adult			</a>
		</li>
			<li>
			<a href="/other/" class="">
				Other			</a>
		</li>
	</ul>		</nav>
	</div>
</header>

<div class="container-fluid">
	<div class="row flex-xl-nowrap">
		<div class="main-container container">
							<div class="col-12 col-md-12 col-xl-10 py-md-3 bd-content main-block">
			
        <style>
		.table th,
		.table td {
			padding: 2px 6px;
		}
		</style>
<div class="card card-nav-tabs main-raised">
	<h5 class="card-header card-header-primary">
		<strong>Deadpool 2016</strong> results <strong>1 - 25</strong> from <strong>500</strong>
										in <strong>movies</strong>																																						</h5>
	<div class="card-body">		
									<ul class="nav nav-tabs" id="tab-detail" style="margin-bottom: 20px;">
											<li class="nav-item">
							<a class="nav-link " href="/search/?q=Deadpool+2016">
																All 							</a>
						</li>
											<li class="nav-item">
							<a class="nav-link active" href="/search/?c=movies&amp;q=Deadpool+2016">
																											<i class="material-icons md-18 local_movies"></i> 
																									Movies <i class="menuValue">500</i>							</a>
						</li>
											<li class="nav-item">
							<a class="nav-link " href="/search/?c=tv&amp;q=Deadpool+2016">
																											<i class="material-icons md-18 movie"></i> 
																									TV <i class="menuValue">386</i>							</a>
						</li>
											<li class="nav-item">
							<a class="nav-link " href="/search/?c=music&amp;q=Deadpool+2016">
																											<i class="material-icons md-18 library_music"></i> 
																									Music <i class="menuValue">4</i>							</a>
						</li>
											<li class="nav-item">
							<a class="nav-link " href="/search/?c=books&amp;q=Deadpool+2016">
																											<i class="material-icons md-18 library_books"></i> 
																									Books <i class="menuValue">6</i>							</a>
						</li>
											<li class="nav-item">
							<a class="nav-link " href="/search/?c=other&amp;q=Deadpool+2016">
																											<i class="material-icons md-18 dehaze"></i> 
																									Other <i class="menuValue">2</i>							</a>
						</li>
									</ul>	
						<div class="table-responsive">
				<table class="table table-striped table-hover search-table">
					<thead>
						<tr>
							<th class="text-left th-tname">TORRENT NAME</th>
																																	<th><a class="sort-link" href="/search/?order=size&amp;sort=desc&amp;c=movies&amp;q=Deadpool+2016">SIZE <i class="sorting fa fa-sort-desc" aria-hidden="true"></i></a></th>
																										<th><a class="sort-link" href="/search/?order=files&amp;sort=desc&amp;c=movies&amp;q=Deadpool+2016">FILES <i class="sorting fa fa-sort-desc" aria-hidden="true"></i></a></th>
																										<th><a class="sort-link" href="/search/?order=age&amp;sort=desc&amp;c=movies&amp;q=Deadpool+2016">AGE <i class="sorting fa fa-sort-desc" aria-hidden="true"></i></a></th>
																										<th><a class="sort-link" href="/search/?order=seed&amp;sort=desc&amp;c=movies&amp;q=Deadpool+2016">SEED <i class="sorting fa fa-sort-desc" aria-hidden="true"></i></a></th>
																										<th><a class="sort-link" href="/search/?order=leech&amp;sort=desc&amp;c=movies&amp;q=Deadpool+2016">LEECH <i class="sorting fa fa-sort-desc" aria-hidden="true"></i></a></th>
																															<th class="th-tname th-source">SOURCE</th>
						</tr>
					</thead>
					<tbody>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-1080p-bluray-yts-yify-1021852/"><b><span>Deadpool</span> (<span>2016</span>) [1080p] [YTS AG] - YIFY</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/highres-movies/"><strong>Highres Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="1021852" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:6268abccb049444bee76813177aa46643a7ada88"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">1020</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>1.65 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>8 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>1.65 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>2</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>8 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">1020</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">389</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-1080p-bluray-yts-yify-1021852/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-1080p-bluray-x264-dts-jyk-3418530/"><b><span>Deadpool</span> <span>2016</span> 1080p BluRay x264 DTS-JYK</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/highres-movies/"><strong>Highres Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="3418530" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:0F61C0478326C8E2F8A397F59D7917A0DC558718"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">327</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>2.7 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>8 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>2.7 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>6</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>8 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">327</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">87</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-1080p-bluray-x264-dts-jyk-3418530/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-720p-bluray-yts-yify-1021851/"><b><span>Deadpool</span> (<span>2016</span>) [720p] [YTS AG] - YIFY</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/highres-movies/"><strong>Highres Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="1021851" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:a1d0c3b0fd52a29d2487027e6b50f27eaf4912c5"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">325</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>798.59 MB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>8 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>798.59 MB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>2</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>8 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">325</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">373</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-720p-bluray-yts-yify-1021851/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-2160p-4k-bluray-yts-yify-9558457/"><b><span>Deadpool</span> (<span>2016</span>) 2160p 4k BluRay YTS YIFY</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/ultrahd/"><strong>UltraHD</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="9558457" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:3697f869f370e0dd35c65a35e8a62a11401edb17"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">311</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>6.01 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>2 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>6.01 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>3</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>2 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">311</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">208</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-2160p-4k-bluray-yts-yify-9558457/#technical" class="source-link-tor">
												<img src="/static/img/source/yts.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-1080p-bluray-ddp5-1-x265-10bit-galaxyrg265-15127494/"><b><span>Deadpool</span>.<span>2016</span>.1080p.BluRay.DDP5.1.x265.10bit-GalaxyRG265</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/highres-movies/"><strong>Highres Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="15127494" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:7411E720C43010F0B945E37F7CCD96EB77D864FF"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">237</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>2.6 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>1 week ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>2.6 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>4</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>1 week ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">237</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">76</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-1080p-bluray-ddp5-1-x265-10bit-galaxyrg265-15127494/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-uhd-bluray-2160p-truehd-atmos-7-1-dv-hevc-hybrid-remux-framestor-9033562/"><b><span>Deadpool</span> <span>2016</span> UHD BluRay 2160p TrueHD Atmos 7 1 DV HEVC HYBRiD REMUX-FraMeSToR</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/highres-movies/"><strong>Highres Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="9033562" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:E4F5D7A2F3DD6B7B1826BD77E316B6B5BA31EB72"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">88</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>40.3 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>1 year ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>40.3 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>1</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>1 year ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">88</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">224</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-uhd-bluray-2160p-truehd-atmos-7-1-dv-hevc-hybrid-remux-framestor-9033562/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-1080p-web-dl-eng-latino-castellano-ddp-5-1-atmos-h264-ben-the-men-14815834/"><b><span>Deadpool</span>.<span>2016</span>.1080p.WEB-DL.ENG.LATINO.CASTELLANO.DDP.5.1.Atmos.H264-BEN.THE.MEN</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/highres-movies/"><strong>Highres Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="14815834" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:BC97659ED6C073102223039C691E029DE17BD706"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">79</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>6.26 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>5 months ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>6.26 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>4</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>5 months ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">79</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">45</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-1080p-web-dl-eng-latino-castellano-ddp-5-1-atmos-h264-ben-the-men-14815834/#technical" class="source-link-tor">
												<img src="/static/img/source/tpb.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-hdts-x264-readnfo-exclusive-2930175/"><b><span>Deadpool</span> (<span>2016</span>) HDTS x264 READNFO - Exclusive</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="2930175" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:61ECD1D1D88B8CEB8DEA36A0E472FA1E11E8AAAC"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">54</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>1.4 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>8 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>1.4 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>2</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>8 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">54</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">5</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-hdts-x264-readnfo-exclusive-2930175/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-proper-2160p-bluray-remux-hevc-dts-hd-ma-truehd-7-1-atmos-fgt-12498904/"><b><span>Deadpool</span>.<span>2016</span>.PROPER.2160p.BluRay.REMUX.HEVC.DTS-HD.MA.TrueHD.7.1.Atmos-FGT</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/ultrahd/"><strong>UltraHD</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="12498904" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:FC8EC150CABD6CAAA9B8613D2FB244AD760E0374"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">52</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>44.53 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>1 year ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>44.53 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>1</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>1 year ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">52</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">26</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-proper-2160p-bluray-remux-hevc-dts-hd-ma-truehd-7-1-atmos-fgt-12498904/#technical" class="source-link-tor">
												<img src="/static/img/source/rarbg.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-4k-2160p-bluray-x265-hevc-10bit-aac-7-1-joy-utr-123406/"><b><span>Deadpool</span> (<span>2016</span>) (4K 2160p BluRay x265 HEVC 10bit AAC 7 1 Joy) [UTR]</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/ultrahd/"><strong>UltraHD</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="123406" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:AF01583C226CDB99EDCC53795EB34F78984E8F97"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">50</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>5.64 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>5 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>5.64 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>11</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>5 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">50</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">33</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-4k-2160p-bluray-x265-hevc-10bit-aac-7-1-joy-utr-123406/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-1080p-bluray-remux-avc-dts-hd-ma-7-1-rarbg-12051652/"><b><span>Deadpool</span>.<span>2016</span>.1080p.BluRay.REMUX.AVC.DTS-HD.MA.7.1-RARBG</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/ultrahd/"><strong>UltraHD</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="12051652" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:45A0C94CE01EF29C6D31990A121301DB139D625B"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">39</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>24.2 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>8 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>24.2 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>1</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>8 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">39</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">19</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-1080p-bluray-remux-avc-dts-hd-ma-7-1-rarbg-12051652/#technical" class="source-link-tor">
												<img src="/static/img/source/rarbg.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-1080p-bluray-x265-rarbg-12123167/"><b><span>Deadpool</span>.<span>2016</span>.1080p.BluRay.x265-RARBG</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="12123167" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:B2DFBA43E729CB2928AB5B88988BA79A2198CD2D"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">35</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>1.69 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>4 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>1.69 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>1</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>4 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">35</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">46</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-1080p-bluray-x265-rarbg-12123167/#technical" class="source-link-tor">
												<img src="/static/img/source/rarbg.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-x264-720p-bluray-eng-subs-dual-audio-hindi-5-1-english-5-1-downloadhub-3453723/"><b><span>Deadpool</span> (<span>2016</span>) x264 720p BluRay Eng Subs {Dual Audio} [Hindi 5 1 + English 5 1] - Downloadhub</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/dubbed-movies/"><strong>Dubbed Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="3453723" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:2DECF5E42220711ACF7A2515ED14EE78F13413FE"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">30</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>983.4 MB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>8 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>983.4 MB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>4</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>8 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">30</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">23</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-x264-720p-bluray-eng-subs-dual-audio-hindi-5-1-english-5-1-downloadhub-3453723/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-2160p-bluray-x265-ddp-atmos-kingdom-15123083/"><b><span>Deadpool</span> <span>2016</span> 2160p Bluray x265 DDP+Atmos-KiNGDOM</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="15123083" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:FFB68CF23554FC143CCAB01B0F4B5B76D99CECE8"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">28</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>10.7 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>1 week ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>10.7 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>6</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>1 week ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">28</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">35</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-2160p-bluray-x265-ddp-atmos-kingdom-15123083/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-720p-hindi-dubbed-english-hdrip-x264-ac3-esub-by-full4movies-3246307/"><b><span>Deadpool</span> (<span>2016</span>) 720p [Hindi Dubbed + English] HDRip x264 AC3 ESub by Full4movies</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="3246307" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:1272C4AEF2E2F883F61BCEBD9CEAB827C58AF403"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">27</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>1 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>6 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>1 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>1</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>6 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">27</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">10</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-720p-hindi-dubbed-english-hdrip-x264-ac3-esub-by-full4movies-3246307/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-2160p-bluray-x265-hevc-10bit-hdr-aac-7-1-tigole-qxr-118795/"><b><span>Deadpool</span> (<span>2016</span>) (2160p BluRay x265 HEVC 10bit HDR AAC 7 1 Tigole) [QxR]</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="118795" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:905671CF23D32AB7FCBC4747DE56A239E2E0F02D"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">27</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>10.36 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>5 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>10.36 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>1</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>5 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">27</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">29</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-2160p-bluray-x265-hevc-10bit-hdr-aac-7-1-tigole-qxr-118795/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-1080p-bluray-x265-hevc-10bit-aac-7-1-tigole-qxr-96002/"><b><span>Deadpool</span> (<span>2016</span>) (1080p BluRay x265 HEVC 10bit AAC 7 1 Tigole) [QxR]</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="96002" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:C31438DA6978494BE3267526A586381C41A05853"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">27</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>5.23 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>5 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>5.23 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>7</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>5 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">27</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">20</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-1080p-bluray-x265-hevc-10bit-aac-7-1-tigole-qxr-96002/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-2160p-multi-uhd-2160p-bluray-x265-hdr-atmos-7-1-en-desi-dtone-118394/"><b><span>Deadpool</span> <span>2016</span> 2160p MULTi UHD 2160p BluRay x265 HDR Atmos 7 1[En+Desi]-DTOne</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/dubbed-movies/"><strong>Dubbed Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="118394" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:894775502A3E051A5AE90BA35F6C84A975E5DA7B"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">27</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>15.97 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>5 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>15.97 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>3</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>5 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">27</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">4</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-2160p-multi-uhd-2160p-bluray-x265-hdr-atmos-7-1-en-desi-dtone-118394/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-new-hd-telesync-v2-x264-cpg-2941770/"><b><span>Deadpool</span> <span>2016</span> NEW HD-TELESYNC V2 x264-CPG</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="2941770" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:B085E7C5D75B99AC8AEF43C63A487E6EC06635CE"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">24</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>1.4 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>8 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>1.4 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>3</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>8 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">24</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">5</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-new-hd-telesync-v2-x264-cpg-2941770/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-bluray-720p-900mb-ganool-2948859/"><b><span>Deadpool</span> (<span>2016</span>) BluRay 720p 900MB Ganool</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																							- <a href="/movies/highres-movies/"><strong>Highres Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="2948859" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:FE4BC738B37B2D13AD6EDF4CA3C6680855ED42FD"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">19</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>901.4 MB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>6 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>901.4 MB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>1</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>6 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">19</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">6</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-bluray-720p-900mb-ganool-2948859/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-720p-hc-hdrip-800mb-mkvcage-3142176/"><b><span>Deadpool</span> (<span>2016</span>) 720p HC HDRip 800MB - MkvCage</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="3142176" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:A70C8F8070C3D0B04B848A5FB044212BF760203F"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">18</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>803.3 MB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>8 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>803.3 MB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>1</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>8 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">18</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">1</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-720p-hc-hdrip-800mb-mkvcage-3142176/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-hd-ts-x264-cpg-2933595/"><b><span>Deadpool</span> <span>2016</span> HD-TS x264-CPG</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="2933595" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:AA23C0591E833A78F0F9D7830030364A07C6B097"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">18</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>844.7 MB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>8 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>844.7 MB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>4</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>8 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">18</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">4</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-hd-ts-x264-cpg-2933595/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-2160p-dolby-vision-and-hdr10-multi-sub-dd5-1-dv-x265-mp4-ben-the-men-12680083/"><b><span>Deadpool</span> <span>2016</span> 2160p Dolby Vision And HDR10 Multi Sub DD5 1 DV x265 MP4-BEN THE MEN</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="12680083" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:BFE6BCC60A12BDD0FB18A5B1C07DCBF6D93E0647"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">18</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>34.7 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>1 year ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>34.7 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>1</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>1 year ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">18</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">29</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-2160p-dolby-vision-and-hdr10-multi-sub-dd5-1-dv-x265-mp4-ben-the-men-12680083/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-1080p-10bit-ds4k-hdr-blu-ray-org-bd-dd5-1-hindi-ddp7-1-english-esub-hevc-nmct-14954355/"><b><span>Deadpool</span>.<span>2016</span>.1080p.10bit.DS4K.HDR.Blu-ray.[Org.BD.DD5.1-Hindi+DDP7.1-English].ESub.HEVC~NmCT</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="14954355" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:9AF6FBC80490B25DB520CE456DEBBC214AFC86B4"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">16</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>6.5 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>3 months ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>6.5 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>1</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>3 months ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">16</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">214</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-1080p-10bit-ds4k-hdr-blu-ray-org-bd-dd5-1-hindi-ddp7-1-english-esub-hevc-nmct-14954355/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
													<tr>
								<td class="text-left">
									<div class="float-left">
																					<i class="material-icons md-18 local_movies"></i>
										<a href="/deadpool-2016-720p-blu-ray-dual-audio-english-hindi-bd-5-1-2279277/"><b><span>Deadpool</span> (<span>2016</span>) 720p Blu-Ray [Dual-Audio][English + Hindi BD 5 1]</b></a>
										<div class="related-posted">
											Posted 
																						in <a href="/movies/"><strong>Movies</strong></a>
																				
										</div>
									</div>								
									<div class="btn-blocks float-right">
																				
																																	<a class="vide-watch-btn" href="/deadpool-m64/watch/"><i class="material-icons play_circle_outline"></i></a>
																																	
										
																				<a class="dwn-btn torrent-dwn" data-id="2279277" target="_blank" rel="nofollow" href="magnet:?xt=urn:btih:C2A6DD91188CEDDD0E1CF14E3CA3C4578D2DD72E"><i class="material-icons file_download"></i></a>
									</div>
									<div class="clearfix"></div>
									<div class="mobile-info-block">
										<div class="mobile-info">
											<i class="material-icons">file_upload</i>
											<span class="text-success">15</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">storage</i>
											<span>1 GB</span>
										</div>
										<div class="mobile-info">
											<i class="material-icons">access_time</i>
											<span>8 years ago</span>
										</div>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Size</span>
										<span>1 GB</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Files</span>
										<span>3</span>
									</div>
								</td>
								<td class="nowrap-td hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Age</span>
										<span>8 years ago</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Seeds</span>
										<span class="text-success">15</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Leechs</span>
										<span class="text-danger">2</span>
									</div>
								</td>
								<td class="hide-on-mob">
									<div class="add-block-wrapper">
										<span class="add-block">Source</span>
																															<a href="/deadpool-2016-720p-blu-ray-dual-audio-english-hindi-bd-5-1-2279277/#technical" class="source-link-tor">
												<img src="/static/img/source/1337x.png" alt="">
											</a>
																			</div>
								</td>								
							</tr>
											</tbody>
				</table>
												
			</div>
						</div>
	
<div class="pagination-block">
	<a class="page-link" style="display:none;">&lt;&lt;</a>
			<a class="page-link is-active">1</a>
		
		
			<a class="page-link " href="/search/deadpool-2016/2/?c=movies">2</a>
			<a class="page-link " href="/search/deadpool-2016/3/?c=movies">3</a>
			<a class="page-link " href="/search/deadpool-2016/4/?c=movies">4</a>
			<a class="page-link " href="/search/deadpool-2016/5/?c=movies">5</a>
		
			<a class="page-link dotted-link">...</a>
		
	
			<a class="page-link " href="/search/deadpool-2016/20/?c=movies">20</a>
		
	<a class="page-link" href="/search/deadpool-2016/2/?c=movies">&gt;&gt;</a>
</div>
	
</div>
				</div>
															<div class="d-xl-block col-xl-2 bd-toc py-md-3">
											<div class="card card-nav-tabs main-raised">
							<h4 class="card-title-header-block">Info</h4>
							
<ul class="list-group list-group-flush">
				<li class="list-group-item"><a href="/news/site-updates/">Dark Mode</a><div class="hr-line"></div></li>
			<li class="list-group-item"><a href="/news/site-updates/">Site Updates</a><div class="hr-line"></div></li>
			<li class="list-group-item"><a href="/news/all-torrents-to-all/">All torrents to All</a><div class="hr-line"></div></li>
	</ul>						
						</div>

		
						<div class="card card-nav-tabs main-raised">
							<h4 class="card-title-header-block">Latest Searches</h4>
							
<div class="list-group">
			<a href="/search/the-good-doctor-s07/" class="list-group-item list-group-item-action flex-column align-items-start search-history-link">
			<p class="mb-1"><i class="material-icons md-16 search"></i>the good doctor s07</p>
			<div class="hr-line search-days-ago">just now</div>
		</a>
			<a href="/search/adult-p2p/" class="list-group-item list-group-item-action flex-column align-items-start search-history-link">
			<p class="mb-1"><i class="material-icons md-16 search"></i>adult p2p</p>
			<div class="hr-line search-days-ago">1 second ago</div>
		</a>
			<a href="/search/titanic-in-colour/" class="list-group-item list-group-item-action flex-column align-items-start search-history-link">
			<p class="mb-1"><i class="material-icons md-16 search"></i>titanic in colour</p>
			<div class="hr-line search-days-ago">1 second ago</div>
		</a>
			<a href="/search/dtf-sluts-22-04-18/" class="list-group-item list-group-item-action flex-column align-items-start search-history-link">
			<p class="mb-1"><i class="material-icons md-16 search"></i>dtf sluts 22 04 18</p>
			<div class="hr-line search-days-ago">1 second ago</div>
		</a>
			<a href="/search/jacquie-et-michel-tv-13/" class="list-group-item list-group-item-action flex-column align-items-start search-history-link">
			<p class="mb-1"><i class="material-icons md-16 search"></i>jacquie et michel tv 13</p>
			<div class="hr-line search-days-ago">1 second ago</div>
		</a>
	</div>						
						</div>
						 
						 																				
								
						<div class="card card-nav-tabs main-raised">
							<h4 class="card-title-header-block">Popular Tags</h4>
							
<div class="tags-block">
		<a href="/search/?order=age&amp;sort=desc&amp;q=yts" class="badge badge-primary">#yts</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=iTALiAN" class="badge badge-primary">#iTALiAN</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=GalaxyTV" class="badge badge-primary">#GalaxyTV</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=ITA" class="badge badge-primary">#ITA</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=eztv" class="badge badge-primary">#eztv</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=hevc+psa" class="badge badge-primary">#hevc-psa</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=miok" class="badge badge-primary">#miok</a>
		<a href="/search/?order=age&amp;sort=desc&amp;c=books&amp;q=Nem" class="badge badge-primary">#Nem</a>
		<a href="/search/?c=games&amp;order=age&amp;sort=desc&amp;q=FitGirl+Repack" class="badge badge-primary">#FitGirl</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=PMEDIA" class="badge badge-primary">#PMEDIA</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=QxR" class="badge badge-primary">#QxR</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=MIRCrew" class="badge badge-primary">#MIRCrew</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=french" class="badge badge-primary">#french</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=TGx" class="badge badge-primary">#TGx</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=MeGusta" class="badge badge-primary">#MeGusta</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=rarbg" class="badge badge-primary">#rarbg</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=hindi" class="badge badge-primary">#Hindi</a>
		<a href="/search/?order=age&amp;sort=desc&amp;q=GalaxyRG" class="badge badge-primary">#GalaxyRG</a>
	</div>							
						</div>
												
					</div>
							</div>
		</div>
	</div>

	<footer class="footer footer-white">
		<div class="container">
			<!--<a class="footer-brand" href="/">
									ext.to							</a>-->
			        		<a class="footer-brand" href="/">All torrents to All</a>
            			            					<ul class="pull-center">
							
			<li><a href="/browse/">Browse</a></li>
							
			<li><a href="/contact/">Contact with us</a></li>
									<li>
					<a href="#" class="js-dark-mode" data-dark-mode="0">
						Dark&nbsp;mode:&nbsp;<span>On</span>
					</a>
				</li>
					
			<li><a target="_blank" href="https://njal.la">njal.la</a></li>
			</ul>
			<div class="kopimi pull-right">
				<a target="_blank" href="https://kopimi.com/kopimi/">
					<img src="/static/img/kopimi30.png" alt="">
				</a>
			</div>			
		</div>
	</footer>

			<div class="modal fade common-modal" id="loginModal" tabindex="-1" role="dialog">
			<div class="modal-dialog modal-login" role="document">
				<div class="modal-content">
					<div class="card card-signup card-plain">
						<div class="modal-header">
							<div class="card-header card-header-primary text-center">
								<button type="button" class="close" data-dismiss="modal" aria-hidden="true"><i class="material-icons clear"></i></button>
								<h4 class="card-title">Sign in</h4>
							</div>
						</div>
						<div class="modal-body">
							<form class="form" id="auth-form">
								<div class="card-body">
									<div class="form-group bmd-form-group">
										<div class="input-group">
											<span class="input-group-addon">
											<i class="material-icons perm_identity"></i>
											</span>
											<input type="text" class="form-control" name="name" placeholder="Nickname" required="">
										</div>
									</div>

									<div class="form-group bmd-form-group">
										<div class="input-group">
											<span class="input-group-addon">
											<i class="material-icons lock_outline"></i>
											</span>
											<input type="password" name="password" placeholder="Password" class="form-control" autocomplete="current-password" required="">
										</div>
									</div>
								</div>
								<p class="text-right">
									<a href="javascript:void(0);" id="recovery-modal-btn" class="special-link" data-toggle="modal" data-target="#recoveryModal">Account recovery</a>
								</p>
								<div class="modal-footer justify-content-center">
									<button type="submit" class="btn btn-primary btn-link btn-wd btn-lg">Log in</button>
								</div>
								<div class="message-box"></div>
							</form>
						</div>
					</div>
				</div>
			</div>
		</div>

		<div class="modal fade common-modal" id="registerModal" tabindex="-1" role="dialog">
			<div class="modal-dialog modal-login" role="document">
				<div class="modal-content">
					<div class="card card-signup card-plain">
						<div class="modal-header">
							<div class="card-header card-header-primary text-center">
								<button type="button" class="close" data-dismiss="modal" aria-hidden="true"><i class="material-icons clear"></i></button>
								<h4 class="card-title">Sign up</h4>
							</div>
						</div>
						<div class="modal-body">
							<form class="form" id="reg-form">
								<div class="card-body">
									<div class="form-group bmd-form-group">
										<div class="input-group">
											<span class="input-group-addon">
											<i class="material-icons perm_identity"></i>
											</span>
											<input type="text" class="form-control" name="name" placeholder="Nickname" required="">
										</div>
									</div>
									
									
									<div class="form-group bmd-form-group">
										<div class="input-group">
											<span class="input-group-addon">
											<i class="material-icons lock_outline"></i>
											</span>
											<input type="password" name="password" placeholder="Password" autocomplete="new-password" class="form-control" required="">
										</div>
									</div>
									
									<div class="form-group bmd-form-group">
										<div class="input-group">
											<span class="input-group-addon">
											<i class="material-icons lock_outline"></i>
											</span>
											<input type="password" name="password2" placeholder="Repeat password" autocomplete="new-password" class="form-control" required="">
										</div>
									</div>
									
									<div class="form-group bmd-form-group">
										<div class="input-group">
											<span class="input-group-addon">
											<i class="material-icons email"></i>
											</span>
											<input type="email" class="form-control" name="email" placeholder="Recovery e-mail (optional)">
										</div>
									</div>
									
									<div class="form-group bmd-form-group">
										<div class="input-group">
											<span class="input-group-addon">
												<i class="material-icons android"></i>
											</span>
											<input type="text" name="captcha_word" placeholder="Antispam code" class="form-control" required="">					
										</div>
										<div class="captcha-block">
																						<img id="captcha-image-code" src="/static/img/kopimi30.png" alt="">
											<input type="hidden" id="captcha-input-code" name="captcha_code">
											<a href="javascript:void(0);" id="captcha-refresh" class="captcha-refresh-btn"><i class="material-icons refresh"></i></a>
										</div>
									</div>						
								</div>
								
								<div class="modal-footer justify-content-center">
									<button type="submit" class="btn btn-primary btn-link btn-wd btn-lg">Register</button>
								</div>
								<div class="message-box"></div>
							</form>
						</div>
					</div>
				</div>
			</div>
		</div>	
		
		<div class="modal fade common-modal" id="recoveryModal" tabindex="-1" role="dialog">
			<div class="modal-dialog modal-login" role="document">
				<div class="modal-content">
					<div class="card card-signup card-plain">
						<div class="modal-header">
							<div class="card-header card-header-primary text-center">
								<button type="button" class="close" data-dismiss="modal" aria-hidden="true"><i class="material-icons clear"></i></button>
								<h4 class="card-title">Account recovery</h4>
							</div>
						</div>
						<div class="modal-body">
							<form class="form" id="password-recovery-form">
								<div class="card-body">
									<div class="form-group bmd-form-group">
										<div class="input-group">
											<span class="input-group-addon">
											<i class="material-icons email"></i>
											</span>
											<input type="email" class="form-control" name="email" placeholder="E-mail" required="">
										</div>
									</div>
								</div>
								<div class="modal-footer justify-content-center">
									<button type="submit" class="btn btn-primary btn-link btn-wd btn-lg">Recover</button>
								</div>
								<div class="message-box"></div>
							</form>
						</div>
					</div>
				</div>
			</div>
		</div>	

				
					
			
	

				

						
	<script type="text/javascript" src="/static/js/core/jquery.min.js?1546462257145741"></script>
<script type="text/javascript" src="/static/js/core/popper.min.js?154646225733477"></script>
<script type="text/javascript" src="/static/js/bootstrap-material-design.min.js?1699473796174945"></script>
<script type="text/javascript" src="/static/js/plugins/moment.min.js?154646225781780"></script>
<script type="text/javascript" src="/static/js/plugins/bootstrap-datetimepicker.min.js?154646225760919"></script>
<script type="text/javascript" src="/static/js/plugins/nouislider.min.js?49916250026465"></script>
<script type="text/javascript" src="/static/js/kit.min.js?16356903858576"></script>
<script type="text/javascript" src="/static/js/main.min.js?171200089316301"></script>
<script type="text/javascript" src="/static/js/no-auth-user.min.js?15807520731534"></script>

<script type="text/javascript">
	window['x4G9Tq2Kw6R7v1Dy3P0B5N8Lc9M2zF']={"adserverDomain":"kzvcggahkgm.com","selPath":"\/d3.php","adbVersion":"3-swf2","suv5":{"cdnPath":"\/script\/kl1Mnopq.js","selPath":"\/d3.php","selAdTypeParam":"m=suv5"},"ippg":{"cdnPath":"\/script\/main_script_123.js","selAdTypeParam":"m=ippg"},"atag":{"cdnPath":"\/script\/index_abc_99.js","selAdTypeParam":"m=atg"},"atagv2":{"cdnPath":"\/script\/atgv2.js"},"intrf":{"selAdTypeParam":"m=intrf"},"intro":{"selAdTypeParam":"m=intro"},"intrn":{"cdnPath":"\/script\/intrn.js","selAdTypeParam":"m=intrn"},"ut":{"cdnPath":"\/script\/ut.js"},"cdnDomain":"jacwkbauzs.com"};!function(){var e={145:function(e,t,i){e.exports=i(6104)},653:function(e,t,i){e.exports=i(7392)},7412:function(e,t,i){e.exports=i(6201)},9524:function(e,t,i){e.exports=i(899)},4071:function(e,t,i){e.exports=i(2066)},2608:function(e,t,i){e.exports=i(1491)},7950:function(e,t,i){e.exports=i(7017)},4369:function(e,t,i){e.exports=i(2590)},8001:function(e,t,i){e.exports=i(9640)},5103:function(e,t,i){e.exports=i(2480)},2243:function(e,t,i){e.exports=i(8864)},1879:function(e,t,i){e.exports=i(7010)},8462:function(e,t,i){e.exports=i(5825)},8333:function(e,t,i){e.exports=i(7186)},111:function(e,t,i){e.exports=i(6832)},8607:function(e,t,i){e.exports=i(9208)},576:function(e,t,i){e.exports=i(7975)},414:function(e,t,i){e.exports=i(6002)},6013:function(e,t,i){e.exports=i(8512)},7513:function(e,t,i){e.exports=i(4978)},8075:function(e,t,i){e.exports=i(2131)},7286:function(e,t,i){e.exports=i(1478)},353:function(e,t,i){"use strict";i(3131),i(9819);var n=i(8088);e.exports=n.Array.from},3677:function(e,t,i){"use strict";i(9263);var n=i(8088);e.exports=n.Array.isArray},2965:function(e,t,i){"use strict";i(4089),i(3070);var n=i(917);e.exports=n("Array","entries")},3638:function(e,t,i){"use strict";i(1948);var n=i(917);e.exports=n("Array","forEach")},4928:function(e,t,i){"use strict";i(738);var n=i(917);e.exports=n("Array","includes")},7083:function(e,t,i){"use strict";i(4509);var n=i(917);e.exports=n("Array","indexOf")},3027:function(e,t,i){"use strict";i(8429);var n=i(917);e.exports=n("Array","map")},4661:function(e,t,i){"use strict";i(8683);var n=i(917);e.exports=n("Array","splice")},1940:function(e,t,i){"use strict";i(6056);var n=i(8088);e.exports=n.Date.now},4609:function(e,t,i){"use strict";i(8845);var n=i(917);e.exports=n("Function","bind")},5876:function(e,t,i){"use strict";var n=i(5354),r=i(4609),s=Function.prototype;e.exports=function(e){var t=e.bind;return e===s||n(s,e)&&t===s.bind?r:t}},1246:function(e,t,i){"use strict";var n=i(5354),r=i(4928),s=i(8148),o=Array.prototype,a=String.prototype;e.exports=function(e){var t=e.includes;return e===o||n(o,e)&&t===o.includes?r:"string"==typeof e||e===a||n(a,e)&&t===a.includes?s:t}},7265:function(e,t,i){"use strict";var n=i(5354),r=i(7083),s=Array.prototype;e.exports=function(e){var t=e.indexOf;return e===s||n(s,e)&&t===s.indexOf?r:t}},8705:function(e,t,i){"use strict";var n=i(5354),r=i(3027),s=Array.prototype;e.exports=function(e){var t=e.map;return e===s||n(s,e)&&t===s.map?r:t}},1263:function(e,t,i){"use strict";var n=i(5354),r=i(4661),s=Array.prototype;e.exports=function(e){var t=e.splice;return e===s||n(s,e)&&t===s.splice?r:t}},947:function(e,t,i){"use strict";var n=i(5354),r=i(6289),s=String.prototype;e.exports=function(e){var t=e.trim;return"string"==typeof e||e===s||n(s,e)&&t===s.trim?r:t}},9271:function(e,t,i){"use strict";i(1087);var n=i(8088),r=i(8974);n.JSON||(n.JSON={stringify:JSON.stringify}),e.exports=function(e,t,i){return r(n.JSON.stringify,null,arguments)}},5854:function(e,t,i){"use strict";i(9446);var n=i(8088);e.exports=n.Number.isInteger},4029:function(e,t,i){"use strict";i(2597);var n=i(8088);e.exports=n.Number.isNaN},7903:function(e,t,i){"use strict";i(3115);var n=i(8088);e.exports=n.Object.keys},4399:function(e,t,i){"use strict";i(1160);var n=i(8088);e.exports=n.parseFloat},2400:function(e,t,i){"use strict";i(3559);var n=i(8088);e.exports=n.parseInt},5357:function(e,t,i){"use strict";i(5184),i(4089),i(3070),i(9113),i(4072),i(7021),i(6849),i(9412),i(3131);var n=i(8088);e.exports=n.Promise},148:function(e,t,i){"use strict";i(4089),i(3070),i(3116),i(3131);var n=i(8088);e.exports=n.Set},8148:function(e,t,i){"use strict";i(716);var n=i(917);e.exports=n("String","includes")},6289:function(e,t,i){"use strict";i(2249);var n=i(917);e.exports=n("String","trim")},6377:function(e,t,i){"use strict";var n=i(3204),r=i(9374),s=TypeError;e.exports=function(e){if(n(e))return e;throw new s(r(e)+" is not a function")}},5897:function(e,t,i){"use strict";var n=i(8074),r=i(9374),s=TypeError;e.exports=function(e){if(n(e))return e;throw new s(r(e)+" is not a constructor")}},7665:function(e,t,i){"use strict";var n=i(8112),r=String,s=TypeError;e.exports=function(e){if(n(e))return e;throw new s("Can't set "+r(e)+" as a prototype")}},9002:function(e){"use strict";e.exports=function(){}},3366:function(e,t,i){"use strict";var n=i(5354),r=TypeError;e.exports=function(e,t){if(n(t,e))return e;throw new r("Incorrect invocation")}},6802:function(e,t,i){"use strict";var n=i(3367),r=String,s=TypeError;e.exports=function(e){if(n(e))return e;throw new s(r(e)+" is not an object")}},7349:function(e,t,i){"use strict";var n=i(6986);e.exports=n((function(){if("function"==typeof ArrayBuffer){var e=new ArrayBuffer(8);Object.isExtensible(e)&&Object.defineProperty(e,"a",{value:8})}}))},6676:function(e,t,i){"use strict";var n=i(1024).forEach,r=i(3165)("forEach");e.exports=r?[].forEach:function(e){return n(this,e,arguments.length>1?arguments[1]:void 0)}},4275:function(e,t,i){"use strict";var n=i(5109),r=i(400),s=i(68),o=i(4532),a=i(6826),c=i(8074),l=i(8949),d=i(313),u=i(2374),h=i(7994),g=Array;e.exports=function(e){var t=s(e),i=c(this),f=arguments.length,p=f>1?arguments[1]:void 0,v=void 0!==p;v&&(p=n(p,f>2?arguments[2]:void 0));var b,m,y,w,x,k,A=h(t),S=0;if(!A||this===g&&a(A))for(b=l(t),m=i?new this(b):g(b);b>S;S++)k=v?p(t[S],S):t[S],d(m,S,k);else for(x=(w=u(t,A)).next,m=i?new this:[];!(y=r(x,w)).done;S++)k=v?o(w,p,[y.value,S],!0):y.value,d(m,S,k);return m.length=S,m}},4634:function(e,t,i){"use strict";var n=i(6724),r=i(8331),s=i(8949),o=function(e){return function(t,i,o){var a,c=n(t),l=s(c),d=r(o,l);if(e&&i!=i){for(;l>d;)if((a=c[d++])!=a)return!0}else for(;l>d;d++)if((e||d in c)&&c[d]===i)return e||d||0;return!e&&-1}};e.exports={includes:o(!0),indexOf:o(!1)}},1024:function(e,t,i){"use strict";var n=i(5109),r=i(5577),s=i(1832),o=i(68),a=i(8949),c=i(6),l=r([].push),d=function(e){var t=1===e,i=2===e,r=3===e,d=4===e,u=6===e,h=7===e,g=5===e||u;return function(f,p,v,b){for(var m,y,w=o(f),x=s(w),k=a(x),A=n(p,v),S=0,C=b||c,T=t?C(f,k):i||h?C(f,0):void 0;k>S;S++)if((g||S in x)&&(y=A(m=x[S],S,w),e))if(t)T[S]=y;else if(y)switch(e){case 3:return!0;case 5:return m;case 6:return S;case 2:l(T,m)}else switch(e){case 4:return!1;case 7:l(T,m)}return u?-1:r||d?d:T}};e.exports={forEach:d(0),map:d(1),filter:d(2),some:d(3),every:d(4),find:d(5),findIndex:d(6),filterReject:d(7)}},1794:function(e,t,i){"use strict";var n=i(6986),r=i(7602),s=i(9933),o=r("species");e.exports=function(e){return s>=51||!n((function(){var t=[];return(t.constructor={})[o]=function(){return{foo:1}},1!==t[e](Boolean).foo}))}},3165:function(e,t,i){"use strict";var n=i(6986);e.exports=function(e,t){var i=[][e];return!!i&&n((function(){i.call(null,t||function(){return 1},1)}))}},6216:function(e,t,i){"use strict";var n=i(7893),r=i(1911),s=TypeError,o=Object.getOwnPropertyDescriptor,a=n&&!function(){if(void 0!==this)return!0;try{Object.defineProperty([],"length",{writable:!1}).length=1}catch(e){return e instanceof TypeError}}();e.exports=a?function(e,t){if(r(e)&&!o(e,"length").writable)throw new s("Cannot set read only .length");return e.length=t}:function(e,t){return e.length=t}},8137:function(e,t,i){"use strict";var n=i(5577);e.exports=n([].slice)},1399:function(e,t,i){"use strict";var n=i(8137),r=Math.floor,s=function(e,t){var i=e.length;if(i<8)for(var o,a,c=1;c<i;){for(a=c,o=e[c];a&&t(e[a-1],o)>0;)e[a]=e[--a];a!==c++&&(e[a]=o)}else for(var l=r(i/2),d=s(n(e,0,l),t),u=s(n(e,l),t),h=d.length,g=u.length,f=0,p=0;f<h||p<g;)e[f+p]=f<h&&p<g?t(d[f],u[p])<=0?d[f++]:u[p++]:f<h?d[f++]:u[p++];return e};e.exports=s},5348:function(e,t,i){"use strict";var n=i(1911),r=i(8074),s=i(3367),o=i(7602)("species"),a=Array;e.exports=function(e){var t;return n(e)&&(t=e.constructor,(r(t)&&(t===a||n(t.prototype))||s(t)&&null===(t=t[o]))&&(t=void 0)),void 0===t?a:t}},6:function(e,t,i){"use strict";var n=i(5348);e.exports=function(e,t){return new(n(e))(0===t?0:t)}},4532:function(e,t,i){"use strict";var n=i(6802),r=i(4380);e.exports=function(e,t,i,s){try{return s?t(n(i)[0],i[1]):t(i)}catch(t){r(e,"throw",t)}}},4075:function(e,t,i){"use strict";var n=i(7602)("iterator"),r=!1;try{var s=0,o={next:function(){return{done:!!s++}},return:function(){r=!0}};o[n]=function(){return this},Array.from(o,(function(){throw 2}))}catch(e){}e.exports=function(e,t){try{if(!t&&!r)return!1}catch(e){return!1}var i=!1;try{var s={};s[n]=function(){return{next:function(){return{done:i=!0}}}},e(s)}catch(e){}return i}},1721:function(e,t,i){"use strict";var n=i(5577),r=n({}.toString),s=n("".slice);e.exports=function(e){return s(r(e),8,-1)}},3238:function(e,t,i){"use strict";var n=i(1769),r=i(3204),s=i(1721),o=i(7602)("toStringTag"),a=Object,c="Arguments"===s(function(){return arguments}());e.exports=n?s:function(e){var t,i,n;return void 0===e?"Undefined":null===e?"Null":"string"==typeof(i=function(e,t){try{return e[t]}catch(e){}}(t=a(e),o))?i:c?s(t):"Object"===(n=s(t))&&r(t.callee)?"Arguments":n}},8119:function(e,t,i){"use strict";var n=i(3921),r=i(1325),s=i(1576),o=i(5109),a=i(3366),c=i(4214),l=i(9889),d=i(9945),u=i(9880),h=i(6532),g=i(7893),f=i(5342).fastKey,p=i(5126),v=p.set,b=p.getterFor;e.exports={getConstructor:function(e,t,i,d){var u=e((function(e,r){a(e,h),v(e,{type:t,index:n(null),first:void 0,last:void 0,size:0}),g||(e.size=0),c(r)||l(r,e[d],{that:e,AS_ENTRIES:i})})),h=u.prototype,p=b(t),m=function(e,t,i){var n,r,s=p(e),o=y(e,t);return o?o.value=i:(s.last=o={index:r=f(t,!0),key:t,value:i,previous:n=s.last,next:void 0,removed:!1},s.first||(s.first=o),n&&(n.next=o),g?s.size++:e.size++,"F"!==r&&(s.index[r]=o)),e},y=function(e,t){var i,n=p(e),r=f(t);if("F"!==r)return n.index[r];for(i=n.first;i;i=i.next)if(i.key===t)return i};return s(h,{clear:function(){for(var e=p(this),t=e.first;t;)t.removed=!0,t.previous&&(t.previous=t.previous.next=void 0),t=t.next;e.first=e.last=void 0,e.index=n(null),g?e.size=0:this.size=0},delete:function(e){var t=this,i=p(t),n=y(t,e);if(n){var r=n.next,s=n.previous;delete i.index[n.index],n.removed=!0,s&&(s.next=r),r&&(r.previous=s),i.first===n&&(i.first=r),i.last===n&&(i.last=s),g?i.size--:t.size--}return!!n},forEach:function(e){for(var t,i=p(this),n=o(e,arguments.length>1?arguments[1]:void 0);t=t?t.next:i.first;)for(n(t.value,t.key,this);t&&t.removed;)t=t.previous},has:function(e){return!!y(this,e)}}),s(h,i?{get:function(e){var t=y(this,e);return t&&t.value},set:function(e,t){return m(this,0===e?0:e,t)}}:{add:function(e){return m(this,e=0===e?0:e,e)}}),g&&r(h,"size",{configurable:!0,get:function(){return p(this).size}}),u},setStrong:function(e,t,i){var n=t+" Iterator",r=b(t),s=b(n);d(e,t,(function(e,t){v(this,{type:n,target:e,state:r(e),kind:t,last:void 0})}),(function(){for(var e=s(this),t=e.kind,i=e.last;i&&i.removed;)i=i.previous;return e.target&&(e.last=i=i?i.next:e.state.first)?u("keys"===t?i.key:"values"===t?i.value:[i.key,i.value],!1):(e.target=void 0,u(void 0,!0))}),i?"entries":"values",!i,!0),h(t)}}},2711:function(e,t,i){"use strict";var n=i(437),r=i(8168),s=i(5342),o=i(6986),a=i(7872),c=i(9889),l=i(3366),d=i(3204),u=i(3367),h=i(4214),g=i(4018),f=i(4154).f,p=i(1024).forEach,v=i(7893),b=i(5126),m=b.set,y=b.getterFor;e.exports=function(e,t,i){var b,w=-1!==e.indexOf("Map"),x=-1!==e.indexOf("Weak"),k=w?"set":"add",A=r[e],S=A&&A.prototype,C={};if(v&&d(A)&&(x||S.forEach&&!o((function(){(new A).entries().next()})))){var T=(b=t((function(t,i){m(l(t,T),{type:e,collection:new A}),h(i)||c(i,t[k],{that:t,AS_ENTRIES:w})}))).prototype,O=y(e);p(["add","clear","delete","forEach","get","has","set","keys","values","entries"],(function(e){var t="add"===e||"set"===e;!(e in S)||x&&"clear"===e||a(T,e,(function(i,n){var r=O(this).collection;if(!t&&x&&!u(i))return"get"===e&&void 0;var s=r[e](0===i?0:i,n);return t?this:s}))})),x||f(T,"size",{configurable:!0,get:function(){return O(this).collection.size}})}else b=i.getConstructor(t,e,w,k),s.enable();return g(b,e,!1,!0),C[e]=b,n({global:!0,forced:!0},C),x||i.setStrong(b,e,w),b}},4361:function(e,t,i){"use strict";var n=i(5674),r=i(1688),s=i(8448),o=i(4154);e.exports=function(e,t,i){for(var a=r(t),c=o.f,l=s.f,d=0;d<a.length;d++){var u=a[d];n(e,u)||i&&n(i,u)||c(e,u,l(t,u))}}},1313:function(e,t,i){"use strict";var n=i(7602)("match");e.exports=function(e){var t=/./;try{"/./"[e](t)}catch(i){try{return t[n]=!1,"/./"[e](t)}catch(e){}}return!1}},7504:function(e,t,i){"use strict";var n=i(6986);e.exports=!n((function(){function e(){}return e.prototype.constructor=null,Object.getPrototypeOf(new e)!==e.prototype}))},9880:function(e){"use strict";e.exports=function(e,t){return{value:e,done:t}}},7872:function(e,t,i){"use strict";var n=i(7893),r=i(4154),s=i(5723);e.exports=n?function(e,t,i){return r.f(e,t,s(1,i))}:function(e,t,i){return e[t]=i,e}},5723:function(e){"use strict";e.exports=function(e,t){return{enumerable:!(1&e),configurable:!(2&e),writable:!(4&e),value:t}}},313:function(e,t,i){"use strict";var n=i(9248),r=i(4154),s=i(5723);e.exports=function(e,t,i){var o=n(t);o in e?r.f(e,o,s(0,i)):e[o]=i}},1325:function(e,t,i){"use strict";var n=i(4154);e.exports=function(e,t,i){return n.f(e,t,i)}},8381:function(e,t,i){"use strict";var n=i(7872);e.exports=function(e,t,i,r){return r&&r.enumerable?e[t]=i:n(e,t,i),e}},1576:function(e,t,i){"use strict";var n=i(8381);e.exports=function(e,t,i){for(var r in t)i&&i.unsafe&&e[r]?e[r]=t[r]:n(e,r,t[r],i);return e}},1638:function(e,t,i){"use strict";var n=i(8168),r=Object.defineProperty;e.exports=function(e,t){try{r(n,e,{value:t,configurable:!0,writable:!0})}catch(i){n[e]=t}return t}},2065:function(e,t,i){"use strict";var n=i(9374),r=TypeError;e.exports=function(e,t){if(!delete e[t])throw new r("Cannot delete property "+n(t)+" of "+n(e))}},7893:function(e,t,i){"use strict";var n=i(6986);e.exports=!n((function(){return 7!==Object.defineProperty({},1,{get:function(){return 7}})[1]}))},766:function(e,t,i){"use strict";var n=i(8168),r=i(3367),s=n.document,o=r(s)&&r(s.createElement);e.exports=function(e){return o?s.createElement(e):{}}},7418:function(e){"use strict";var t=TypeError;e.exports=function(e){if(e>9007199254740991)throw t("Maximum allowed index exceeded");return e}},2765:function(e){"use strict";e.exports={CSSRuleList:0,CSSStyleDeclaration:0,CSSValueList:0,ClientRectList:0,DOMRectList:0,DOMStringList:0,DOMTokenList:1,DataTransferItemList:0,FileList:0,HTMLAllCollection:0,HTMLCollection:0,HTMLFormElement:0,HTMLSelectElement:0,MediaList:0,MimeTypeArray:0,NamedNodeMap:0,NodeList:1,PaintRequestList:0,Plugin:0,PluginArray:0,SVGLengthList:0,SVGNumberList:0,SVGPathSegList:0,SVGPointList:0,SVGStringList:0,SVGTransformList:0,SourceBufferList:0,StyleSheetList:0,TextTrackCueList:0,TextTrackList:0,TouchList:0}},1931:function(e,t,i){"use strict";var n=i(8259),r=i(3271);e.exports=!n&&!r&&"object"==typeof window&&"object"==typeof document},1162:function(e){"use strict";e.exports="function"==typeof Bun&&Bun&&"string"==typeof Bun.version},8259:function(e){"use strict";e.exports="object"==typeof Deno&&Deno&&"object"==typeof Deno.version},271:function(e,t,i){"use strict";var n=i(2917);e.exports=/ipad|iphone|ipod/i.test(n)&&"undefined"!=typeof Pebble},1730:function(e,t,i){"use strict";var n=i(2917);e.exports=/(?:ipad|iphone|ipod).*applewebkit/i.test(n)},3271:function(e,t,i){"use strict";var n=i(8168),r=i(1721);e.exports="process"===r(n.process)},1694:function(e,t,i){"use strict";var n=i(2917);e.exports=/web0s(?!.*chrome)/i.test(n)},2917:function(e){"use strict";e.exports="undefined"!=typeof navigator&&String(navigator.userAgent)||""},9933:function(e,t,i){"use strict";var n,r,s=i(8168),o=i(2917),a=s.process,c=s.Deno,l=a&&a.versions||c&&c.version,d=l&&l.v8;d&&(r=(n=d.split("."))[0]>0&&n[0]<4?1:+(n[0]+n[1])),!r&&o&&(!(n=o.match(/Edge\/(\d+)/))||n[1]>=74)&&(n=o.match(/Chrome\/(\d+)/))&&(r=+n[1]),e.exports=r},4274:function(e){"use strict";e.exports=["constructor","hasOwnProperty","isPrototypeOf","propertyIsEnumerable","toLocaleString","toString","valueOf"]},724:function(e,t,i){"use strict";var n=i(5577),r=Error,s=n("".replace),o=String(new r("zxcasd").stack),a=/\n\s*at [^:]*:[^\n]*/,c=a.test(o);e.exports=function(e,t){if(c&&"string"==typeof e&&!r.prepareStackTrace)for(;t--;)e=s(e,a,"");return e}},2206:function(e,t,i){"use strict";var n=i(7872),r=i(724),s=i(9246),o=Error.captureStackTrace;e.exports=function(e,t,i,a){s&&(o?o(e,t):n(e,"stack",r(i,a)))}},9246:function(e,t,i){"use strict";var n=i(6986),r=i(5723);e.exports=!n((function(){var e=new Error("a");return!("stack"in e)||(Object.defineProperty(e,"stack",r(1,7)),7!==e.stack)}))},437:function(e,t,i){"use strict";var n=i(8168),r=i(8974),s=i(8355),o=i(3204),a=i(8448).f,c=i(6337),l=i(8088),d=i(5109),u=i(7872),h=i(5674),g=function(e){var t=function(i,n,s){if(this instanceof t){switch(arguments.length){case 0:return new e;case 1:return new e(i);case 2:return new e(i,n)}return new e(i,n,s)}return r(e,this,arguments)};return t.prototype=e.prototype,t};e.exports=function(e,t){var i,r,f,p,v,b,m,y,w,x=e.target,k=e.global,A=e.stat,S=e.proto,C=k?n:A?n[x]:(n[x]||{}).prototype,T=k?l:l[x]||u(l,x,{})[x],O=T.prototype;for(p in t)r=!(i=c(k?p:x+(A?".":"#")+p,e.forced))&&C&&h(C,p),b=T[p],r&&(m=e.dontCallGetSet?(w=a(C,p))&&w.value:C[p]),v=r&&m?m:t[p],r&&typeof b==typeof v||(y=e.bind&&r?d(v,n):e.wrap&&r?g(v):S&&o(v)?s(v):v,(e.sham||v&&v.sham||b&&b.sham)&&u(y,"sham",!0),u(T,p,y),S&&(h(l,f=x+"Prototype")||u(l,f,{}),u(l[f],p,v),e.real&&O&&(i||!O[p])&&u(O,p,v)))}},6986:function(e){"use strict";e.exports=function(e){try{return!!e()}catch(e){return!0}}},8231:function(e,t,i){"use strict";var n=i(6986);e.exports=!n((function(){return Object.isExtensible(Object.preventExtensions({}))}))},8974:function(e,t,i){"use strict";var n=i(8151),r=Function.prototype,s=r.apply,o=r.call;e.exports="object"==typeof Reflect&&Reflect.apply||(n?o.bind(s):function(){return o.apply(s,arguments)})},5109:function(e,t,i){"use strict";var n=i(8355),r=i(6377),s=i(8151),o=n(n.bind);e.exports=function(e,t){return r(e),void 0===t?e:s?o(e,t):function(){return e.apply(t,arguments)}}},8151:function(e,t,i){"use strict";var n=i(6986);e.exports=!n((function(){var e=function(){}.bind();return"function"!=typeof e||e.hasOwnProperty("prototype")}))},2843:function(e,t,i){"use strict";var n=i(5577),r=i(6377),s=i(3367),o=i(5674),a=i(8137),c=i(8151),l=Function,d=n([].concat),u=n([].join),h={};e.exports=c?l.bind:function(e){var t=r(this),i=t.prototype,n=a(arguments,1),c=function(){var i=d(n,a(arguments));return this instanceof c?function(e,t,i){if(!o(h,t)){for(var n=[],r=0;r<t;r++)n[r]="a["+r+"]";h[t]=l("C,a","return new C("+u(n,",")+")")}return h[t](e,i)}(t,i.length,i):t.apply(e,i)};return s(i)&&(c.prototype=i),c}},400:function(e,t,i){"use strict";var n=i(8151),r=Function.prototype.call;e.exports=n?r.bind(r):function(){return r.apply(r,arguments)}},6519:function(e,t,i){"use strict";var n=i(7893),r=i(5674),s=Function.prototype,o=n&&Object.getOwnPropertyDescriptor,a=r(s,"name"),c=a&&"something"===function(){}.name,l=a&&(!n||n&&o(s,"name").configurable);e.exports={EXISTS:a,PROPER:c,CONFIGURABLE:l}},3273:function(e,t,i){"use strict";var n=i(5577),r=i(6377);e.exports=function(e,t,i){try{return n(r(Object.getOwnPropertyDescriptor(e,t)[i]))}catch(e){}}},8355:function(e,t,i){"use strict";var n=i(1721),r=i(5577);e.exports=function(e){if("Function"===n(e))return r(e)}},5577:function(e,t,i){"use strict";var n=i(8151),r=Function.prototype,s=r.call,o=n&&r.bind.bind(s,s);e.exports=n?o:function(e){return function(){return s.apply(e,arguments)}}},917:function(e,t,i){"use strict";var n=i(8168),r=i(8088);e.exports=function(e,t){var i=r[e+"Prototype"],s=i&&i[t];if(s)return s;var o=n[e],a=o&&o.prototype;return a&&a[t]}},9660:function(e,t,i){"use strict";var n=i(8088),r=i(8168),s=i(3204),o=function(e){return s(e)?e:void 0};e.exports=function(e,t){return arguments.length<2?o(n[e])||o(r[e]):n[e]&&n[e][t]||r[e]&&r[e][t]}},7994:function(e,t,i){"use strict";var n=i(3238),r=i(7545),s=i(4214),o=i(5988),a=i(7602)("iterator");e.exports=function(e){if(!s(e))return r(e,a)||r(e,"@@iterator")||o[n(e)]}},2374:function(e,t,i){"use strict";var n=i(400),r=i(6377),s=i(6802),o=i(9374),a=i(7994),c=TypeError;e.exports=function(e,t){var i=arguments.length<2?a(e):t;if(r(i))return s(n(i,e));throw new c(o(e)+" is not iterable")}},3334:function(e,t,i){"use strict";var n=i(5577),r=i(1911),s=i(3204),o=i(1721),a=i(9618),c=n([].push);e.exports=function(e){if(s(e))return e;if(r(e)){for(var t=e.length,i=[],n=0;n<t;n++){var l=e[n];"string"==typeof l?c(i,l):"number"!=typeof l&&"Number"!==o(l)&&"String"!==o(l)||c(i,a(l))}var d=i.length,u=!0;return function(e,t){if(u)return u=!1,t;if(r(this))return t;for(var n=0;n<d;n++)if(i[n]===e)return t}}}},7545:function(e,t,i){"use strict";var n=i(6377),r=i(4214);e.exports=function(e,t){var i=e[t];return r(i)?void 0:n(i)}},8168:function(e,t,i){"use strict";var n=function(e){return e&&e.Math===Math&&e};e.exports=n("object"==typeof globalThis&&globalThis)||n("object"==typeof window&&window)||n("object"==typeof self&&self)||n("object"==typeof i.g&&i.g)||n("object"==typeof this&&this)||function(){return this}()||Function("return this")()},5674:function(e,t,i){"use strict";var n=i(5577),r=i(68),s=n({}.hasOwnProperty);e.exports=Object.hasOwn||function(e,t){return s(r(e),t)}},2028:function(e){"use strict";e.exports={}},1442:function(e){"use strict";e.exports=function(e,t){try{1===arguments.length?console.error(e):console.error(e,t)}catch(e){}}},1322:function(e,t,i){"use strict";var n=i(9660);e.exports=n("document","documentElement")},5630:function(e,t,i){"use strict";var n=i(7893),r=i(6986),s=i(766);e.exports=!n&&!r((function(){return 7!==Object.defineProperty(s("div"),"a",{get:function(){return 7}}).a}))},1832:function(e,t,i){"use strict";var n=i(5577),r=i(6986),s=i(1721),o=Object,a=n("".split);e.exports=r((function(){return!o("z").propertyIsEnumerable(0)}))?function(e){return"String"===s(e)?a(e,""):o(e)}:o},1181:function(e,t,i){"use strict";var n=i(5577),r=i(3204),s=i(7150),o=n(Function.toString);r(s.inspectSource)||(s.inspectSource=function(e){return o(e)}),e.exports=s.inspectSource},7113:function(e,t,i){"use strict";var n=i(3367),r=i(7872);e.exports=function(e,t){n(t)&&"cause"in t&&r(e,"cause",t.cause)}},5342:function(e,t,i){"use strict";var n=i(437),r=i(5577),s=i(2028),o=i(3367),a=i(5674),c=i(4154).f,l=i(1013),d=i(669),u=i(5119),h=i(6665),g=i(8231),f=!1,p=h("meta"),v=0,b=function(e){c(e,p,{value:{objectID:"O"+v++,weakData:{}}})},m=e.exports={enable:function(){m.enable=function(){},f=!0;var e=l.f,t=r([].splice),i={};i[p]=1,e(i).length&&(l.f=function(i){for(var n=e(i),r=0,s=n.length;r<s;r++)if(n[r]===p){t(n,r,1);break}return n},n({target:"Object",stat:!0,forced:!0},{getOwnPropertyNames:d.f}))},fastKey:function(e,t){if(!o(e))return"symbol"==typeof e?e:("string"==typeof e?"S":"P")+e;if(!a(e,p)){if(!u(e))return"F";if(!t)return"E";b(e)}return e[p].objectID},getWeakData:function(e,t){if(!a(e,p)){if(!u(e))return!0;if(!t)return!1;b(e)}return e[p].weakData},onFreeze:function(e){return g&&f&&u(e)&&!a(e,p)&&b(e),e}};s[p]=!0},5126:function(e,t,i){"use strict";var n,r,s,o=i(8993),a=i(8168),c=i(3367),l=i(7872),d=i(5674),u=i(7150),h=i(7552),g=i(2028),f="Object already initialized",p=a.TypeError,v=a.WeakMap;if(o||u.state){var b=u.state||(u.state=new v);b.get=b.get,b.has=b.has,b.set=b.set,n=function(e,t){if(b.has(e))throw new p(f);return t.facade=e,b.set(e,t),t},r=function(e){return b.get(e)||{}},s=function(e){return b.has(e)}}else{var m=h("state");g[m]=!0,n=function(e,t){if(d(e,m))throw new p(f);return t.facade=e,l(e,m,t),t},r=function(e){return d(e,m)?e[m]:{}},s=function(e){return d(e,m)}}e.exports={set:n,get:r,has:s,enforce:function(e){return s(e)?r(e):n(e,{})},getterFor:function(e){return function(t){var i;if(!c(t)||(i=r(t)).type!==e)throw new p("Incompatible receiver, "+e+" required");return i}}}},6826:function(e,t,i){"use strict";var n=i(7602),r=i(5988),s=n("iterator"),o=Array.prototype;e.exports=function(e){return void 0!==e&&(r.Array===e||o[s]===e)}},1911:function(e,t,i){"use strict";var n=i(1721);e.exports=Array.isArray||function(e){return"Array"===n(e)}},3204:function(e){"use strict";var t="object"==typeof document&&document.all;e.exports=void 0===t&&void 0!==t?function(e){return"function"==typeof e||e===t}:function(e){return"function"==typeof e}},8074:function(e,t,i){"use strict";var n=i(5577),r=i(6986),s=i(3204),o=i(3238),a=i(9660),c=i(1181),l=function(){},d=[],u=a("Reflect","construct"),h=/^\s*(?:class|function)\b/,g=n(h.exec),f=!h.test(l),p=function(e){if(!s(e))return!1;try{return u(l,d,e),!0}catch(e){return!1}},v=function(e){if(!s(e))return!1;switch(o(e)){case"AsyncFunction":case"GeneratorFunction":case"AsyncGeneratorFunction":return!1}try{return f||!!g(h,c(e))}catch(e){return!0}};v.sham=!0,e.exports=!u||r((function(){var e;return p(p.call)||!p(Object)||!p((function(){e=!0}))||e}))?v:p},6337:function(e,t,i){"use strict";var n=i(6986),r=i(3204),s=/#|\.prototype\./,o=function(e,t){var i=c[a(e)];return i===d||i!==l&&(r(t)?n(t):!!t)},a=o.normalize=function(e){return String(e).replace(s,".").toLowerCase()},c=o.data={},l=o.NATIVE="N",d=o.POLYFILL="P";e.exports=o},4648:function(e,t,i){"use strict";var n=i(3367),r=Math.floor;e.exports=Number.isInteger||function(e){return!n(e)&&isFinite(e)&&r(e)===e}},4214:function(e){"use strict";e.exports=function(e){return null==e}},3367:function(e,t,i){"use strict";var n=i(3204);e.exports=function(e){return"object"==typeof e?null!==e:n(e)}},8112:function(e,t,i){"use strict";var n=i(3367);e.exports=function(e){return n(e)||null===e}},670:function(e){"use strict";e.exports=!0},6401:function(e,t,i){"use strict";var n=i(3367),r=i(1721),s=i(7602)("match");e.exports=function(e){var t;return n(e)&&(void 0!==(t=e[s])?!!t:"RegExp"===r(e))}},7560:function(e,t,i){"use strict";var n=i(9660),r=i(3204),s=i(5354),o=i(8425),a=Object;e.exports=o?function(e){return"symbol"==typeof e}:function(e){var t=n("Symbol");return r(t)&&s(t.prototype,a(e))}},9889:function(e,t,i){"use strict";var n=i(5109),r=i(400),s=i(6802),o=i(9374),a=i(6826),c=i(8949),l=i(5354),d=i(2374),u=i(7994),h=i(4380),g=TypeError,f=function(e,t){this.stopped=e,this.result=t},p=f.prototype;e.exports=function(e,t,i){var v,b,m,y,w,x,k,A=i&&i.that,S=!(!i||!i.AS_ENTRIES),C=!(!i||!i.IS_RECORD),T=!(!i||!i.IS_ITERATOR),O=!(!i||!i.INTERRUPTED),I=n(t,A),E=function(e){return v&&h(v,"normal",e),new f(!0,e)},R=function(e){return S?(s(e),O?I(e[0],e[1],E):I(e[0],e[1])):O?I(e,E):I(e)};if(C)v=e.iterator;else if(T)v=e;else{if(!(b=u(e)))throw new g(o(e)+" is not iterable");if(a(b)){for(m=0,y=c(e);y>m;m++)if((w=R(e[m]))&&l(p,w))return w;return new f(!1)}v=d(e,b)}for(x=C?e.next:v.next;!(k=r(x,v)).done;){try{w=R(k.value)}catch(e){h(v,"throw",e)}if("object"==typeof w&&w&&l(p,w))return w}return new f(!1)}},4380:function(e,t,i){"use strict";var n=i(400),r=i(6802),s=i(7545);e.exports=function(e,t,i){var o,a;r(e);try{if(!(o=s(e,"return"))){if("throw"===t)throw i;return i}o=n(o,e)}catch(e){a=!0,o=e}if("throw"===t)throw i;if(a)throw o;return r(o),i}},8287:function(e,t,i){"use strict";var n=i(8090).IteratorPrototype,r=i(3921),s=i(5723),o=i(4018),a=i(5988),c=function(){return this};e.exports=function(e,t,i,l){var d=t+" Iterator";return e.prototype=r(n,{next:s(+!l,i)}),o(e,d,!1,!0),a[d]=c,e}},9945:function(e,t,i){"use strict";var n=i(437),r=i(400),s=i(670),o=i(6519),a=i(3204),c=i(8287),l=i(6866),d=i(3718),u=i(4018),h=i(7872),g=i(8381),f=i(7602),p=i(5988),v=i(8090),b=o.PROPER,m=o.CONFIGURABLE,y=v.IteratorPrototype,w=v.BUGGY_SAFARI_ITERATORS,x=f("iterator"),k="keys",A="values",S="entries",C=function(){return this};e.exports=function(e,t,i,o,f,v,T){c(i,t,o);var O,I,E,R=function(e){if(e===f&&F)return F;if(!w&&e&&e in L)return L[e];switch(e){case k:case A:case S:return function(){return new i(this,e)}}return function(){return new i(this)}},P=t+" Iterator",$=!1,L=e.prototype,z=L[x]||L["@@iterator"]||f&&L[f],F=!w&&z||R(f),U="Array"===t&&L.entries||z;if(U&&(O=l(U.call(new e)))!==Object.prototype&&O.next&&(s||l(O)===y||(d?d(O,y):a(O[x])||g(O,x,C)),u(O,P,!0,!0),s&&(p[P]=C)),b&&f===A&&z&&z.name!==A&&(!s&&m?h(L,"name",A):($=!0,F=function(){return r(z,this)})),f)if(I={values:R(A),keys:v?F:R(k),entries:R(S)},T)for(E in I)(w||$||!(E in L))&&g(L,E,I[E]);else n({target:t,proto:!0,forced:w||$},I);return s&&!T||L[x]===F||g(L,x,F,{name:f}),p[t]=F,I}},8090:function(e,t,i){"use strict";var n,r,s,o=i(6986),a=i(3204),c=i(3367),l=i(3921),d=i(6866),u=i(8381),h=i(7602),g=i(670),f=h("iterator"),p=!1;[].keys&&("next"in(s=[].keys())?(r=d(d(s)))!==Object.prototype&&(n=r):p=!0),!c(n)||o((function(){var e={};return n[f].call(e)!==e}))?n={}:g&&(n=l(n)),a(n[f])||u(n,f,(function(){return this})),e.exports={IteratorPrototype:n,BUGGY_SAFARI_ITERATORS:p}},5988:function(e){"use strict";e.exports={}},8949:function(e,t,i){"use strict";var n=i(3315);e.exports=function(e){return n(e.length)}},9718:function(e){"use strict";var t=Math.ceil,i=Math.floor;e.exports=Math.trunc||function(e){var n=+e;return(n>0?i:t)(n)}},4726:function(e,t,i){"use strict";var n,r,s,o,a,c=i(8168),l=i(6028),d=i(5109),u=i(5050).set,h=i(9264),g=i(1730),f=i(271),p=i(1694),v=i(3271),b=c.MutationObserver||c.WebKitMutationObserver,m=c.document,y=c.process,w=c.Promise,x=l("queueMicrotask");if(!x){var k=new h,A=function(){var e,t;for(v&&(e=y.domain)&&e.exit();t=k.get();)try{t()}catch(e){throw k.head&&n(),e}e&&e.enter()};g||v||p||!b||!m?!f&&w&&w.resolve?((o=w.resolve(void 0)).constructor=w,a=d(o.then,o),n=function(){a(A)}):v?n=function(){y.nextTick(A)}:(u=d(u,c),n=function(){u(A)}):(r=!0,s=m.createTextNode(""),new b(A).observe(s,{characterData:!0}),n=function(){s.data=r=!r}),x=function(e){k.head||n(),k.add(e)}}e.exports=x},2668:function(e,t,i){"use strict";var n=i(6377),r=TypeError,s=function(e){var t,i;this.promise=new e((function(e,n){if(void 0!==t||void 0!==i)throw new r("Bad Promise constructor");t=e,i=n})),this.resolve=n(t),this.reject=n(i)};e.exports.f=function(e){return new s(e)}},3586:function(e,t,i){"use strict";var n=i(9618);e.exports=function(e,t){return void 0===e?arguments.length<2?"":t:n(e)}},156:function(e,t,i){"use strict";var n=i(6401),r=TypeError;e.exports=function(e){if(n(e))throw new r("The method doesn't accept regular expressions");return e}},8459:function(e,t,i){"use strict";var n=i(8168),r=i(6986),s=i(5577),o=i(9618),a=i(11).trim,c=i(369),l=s("".charAt),d=n.parseFloat,u=n.Symbol,h=u&&u.iterator,g=1/d(c+"-0")!=-1/0||h&&!r((function(){d(Object(h))}));e.exports=g?function(e){var t=a(o(e)),i=d(t);return 0===i&&"-"===l(t,0)?-0:i}:d},668:function(e,t,i){"use strict";var n=i(8168),r=i(6986),s=i(5577),o=i(9618),a=i(11).trim,c=i(369),l=n.parseInt,d=n.Symbol,u=d&&d.iterator,h=/^[+-]?0x/i,g=s(h.exec),f=8!==l(c+"08")||22!==l(c+"0x16")||u&&!r((function(){l(Object(u))}));e.exports=f?function(e,t){var i=a(o(e));return l(i,t>>>0||(g(h,i)?16:10))}:l},2872:function(e,t,i){"use strict";var n=i(7893),r=i(5577),s=i(400),o=i(6986),a=i(6889),c=i(3860),l=i(7848),d=i(68),u=i(1832),h=Object.assign,g=Object.defineProperty,f=r([].concat);e.exports=!h||o((function(){if(n&&1!==h({b:1},h(g({},"a",{enumerable:!0,get:function(){g(this,"b",{value:3,enumerable:!1})}}),{b:2})).b)return!0;var e={},t={},i=Symbol("assign detection"),r="abcdefghijklmnopqrst";return e[i]=7,r.split("").forEach((function(e){t[e]=e})),7!==h({},e)[i]||a(h({},t)).join("")!==r}))?function(e,t){for(var i=d(e),r=arguments.length,o=1,h=c.f,g=l.f;r>o;)for(var p,v=u(arguments[o++]),b=h?f(a(v),h(v)):a(v),m=b.length,y=0;m>y;)p=b[y++],n&&!s(g,v,p)||(i[p]=v[p]);return i}:h},3921:function(e,t,i){"use strict";var n,r=i(6802),s=i(934),o=i(4274),a=i(2028),c=i(1322),l=i(766),d=i(7552),u="prototype",h="script",g=d("IE_PROTO"),f=function(){},p=function(e){return"<"+h+">"+e+"</"+h+">"},v=function(e){e.write(p("")),e.close();var t=e.parentWindow.Object;return e=null,t},b=function(){try{n=new ActiveXObject("htmlfile")}catch(e){}var e,t,i;b="undefined"!=typeof document?document.domain&&n?v(n):(t=l("iframe"),i="java"+h+":",t.style.display="none",c.appendChild(t),t.src=String(i),(e=t.contentWindow.document).open(),e.write(p("document.F=Object")),e.close(),e.F):v(n);for(var r=o.length;r--;)delete b[u][o[r]];return b()};a[g]=!0,e.exports=Object.create||function(e,t){var i;return null!==e?(f[u]=r(e),i=new f,f[u]=null,i[g]=e):i=b(),void 0===t?i:s.f(i,t)}},934:function(e,t,i){"use strict";var n=i(7893),r=i(4603),s=i(4154),o=i(6802),a=i(6724),c=i(6889);t.f=n&&!r?Object.defineProperties:function(e,t){o(e);for(var i,n=a(t),r=c(t),l=r.length,d=0;l>d;)s.f(e,i=r[d++],n[i]);return e}},4154:function(e,t,i){"use strict";var n=i(7893),r=i(5630),s=i(4603),o=i(6802),a=i(9248),c=TypeError,l=Object.defineProperty,d=Object.getOwnPropertyDescriptor,u="enumerable",h="configurable",g="writable";t.f=n?s?function(e,t,i){if(o(e),t=a(t),o(i),"function"==typeof e&&"prototype"===t&&"value"in i&&g in i&&!i[g]){var n=d(e,t);n&&n[g]&&(e[t]=i.value,i={configurable:h in i?i[h]:n[h],enumerable:u in i?i[u]:n[u],writable:!1})}return l(e,t,i)}:l:function(e,t,i){if(o(e),t=a(t),o(i),r)try{return l(e,t,i)}catch(e){}if("get"in i||"set"in i)throw new c("Accessors not supported");return"value"in i&&(e[t]=i.value),e}},8448:function(e,t,i){"use strict";var n=i(7893),r=i(400),s=i(7848),o=i(5723),a=i(6724),c=i(9248),l=i(5674),d=i(5630),u=Object.getOwnPropertyDescriptor;t.f=n?u:function(e,t){if(e=a(e),t=c(t),d)try{return u(e,t)}catch(e){}if(l(e,t))return o(!r(s.f,e,t),e[t])}},669:function(e,t,i){"use strict";var n=i(1721),r=i(6724),s=i(1013).f,o=i(8137),a="object"==typeof window&&window&&Object.getOwnPropertyNames?Object.getOwnPropertyNames(window):[];e.exports.f=function(e){return a&&"Window"===n(e)?function(e){try{return s(e)}catch(e){return o(a)}}(e):s(r(e))}},1013:function(e,t,i){"use strict";var n=i(2139),r=i(4274).concat("length","prototype");t.f=Object.getOwnPropertyNames||function(e){return n(e,r)}},3860:function(e,t){"use strict";t.f=Object.getOwnPropertySymbols},6866:function(e,t,i){"use strict";var n=i(5674),r=i(3204),s=i(68),o=i(7552),a=i(7504),c=o("IE_PROTO"),l=Object,d=l.prototype;e.exports=a?l.getPrototypeOf:function(e){var t=s(e);if(n(t,c))return t[c];var i=t.constructor;return r(i)&&t instanceof i?i.prototype:t instanceof l?d:null}},5119:function(e,t,i){"use strict";var n=i(6986),r=i(3367),s=i(1721),o=i(7349),a=Object.isExtensible,c=n((function(){a(1)}));e.exports=c||o?function(e){return!!r(e)&&(!o||"ArrayBuffer"!==s(e))&&(!a||a(e))}:a},5354:function(e,t,i){"use strict";var n=i(5577);e.exports=n({}.isPrototypeOf)},2139:function(e,t,i){"use strict";var n=i(5577),r=i(5674),s=i(6724),o=i(4634).indexOf,a=i(2028),c=n([].push);e.exports=function(e,t){var i,n=s(e),l=0,d=[];for(i in n)!r(a,i)&&r(n,i)&&c(d,i);for(;t.length>l;)r(n,i=t[l++])&&(~o(d,i)||c(d,i));return d}},6889:function(e,t,i){"use strict";var n=i(2139),r=i(4274);e.exports=Object.keys||function(e){return n(e,r)}},7848:function(e,t){"use strict";var i={}.propertyIsEnumerable,n=Object.getOwnPropertyDescriptor,r=n&&!i.call({1:2},1);t.f=r?function(e){var t=n(this,e);return!!t&&t.enumerable}:i},3718:function(e,t,i){"use strict";var n=i(3273),r=i(6802),s=i(7665);e.exports=Object.setPrototypeOf||("__proto__"in{}?function(){var e,t=!1,i={};try{(e=n(Object.prototype,"__proto__","set"))(i,[]),t=i instanceof Array}catch(e){}return function(i,n){return r(i),s(n),t?e(i,n):i.__proto__=n,i}}():void 0)},1708:function(e,t,i){"use strict";var n=i(1769),r=i(3238);e.exports=n?{}.toString:function(){return"[object "+r(this)+"]"}},6679:function(e,t,i){"use strict";var n=i(400),r=i(3204),s=i(3367),o=TypeError;e.exports=function(e,t){var i,a;if("string"===t&&r(i=e.toString)&&!s(a=n(i,e)))return a;if(r(i=e.valueOf)&&!s(a=n(i,e)))return a;if("string"!==t&&r(i=e.toString)&&!s(a=n(i,e)))return a;throw new o("Can't convert object to primitive value")}},1688:function(e,t,i){"use strict";var n=i(9660),r=i(5577),s=i(1013),o=i(3860),a=i(6802),c=r([].concat);e.exports=n("Reflect","ownKeys")||function(e){var t=s.f(a(e)),i=o.f;return i?c(t,i(e)):t}},8088:function(e){"use strict";e.exports={}},1618:function(e){"use strict";e.exports=function(e){try{return{error:!1,value:e()}}catch(e){return{error:!0,value:e}}}},5741:function(e,t,i){"use strict";var n=i(8168),r=i(1437),s=i(3204),o=i(6337),a=i(1181),c=i(7602),l=i(1931),d=i(8259),u=i(670),h=i(9933),g=r&&r.prototype,f=c("species"),p=!1,v=s(n.PromiseRejectionEvent),b=o("Promise",(function(){var e=a(r),t=e!==String(r);if(!t&&66===h)return!0;if(u&&(!g.catch||!g.finally))return!0;if(!h||h<51||!/native code/.test(e)){var i=new r((function(e){e(1)})),n=function(e){e((function(){}),(function(){}))};if((i.constructor={})[f]=n,!(p=i.then((function(){}))instanceof n))return!0}return!t&&(l||d)&&!v}));e.exports={CONSTRUCTOR:b,REJECTION_EVENT:v,SUBCLASSING:p}},1437:function(e,t,i){"use strict";var n=i(8168);e.exports=n.Promise},1083:function(e,t,i){"use strict";var n=i(6802),r=i(3367),s=i(2668);e.exports=function(e,t){if(n(e),r(t)&&t.constructor===e)return t;var i=s.f(e);return(0,i.resolve)(t),i.promise}},3948:function(e,t,i){"use strict";var n=i(1437),r=i(4075),s=i(5741).CONSTRUCTOR;e.exports=s||!r((function(e){n.all(e).then(void 0,(function(){}))}))},9264:function(e){"use strict";var t=function(){this.head=null,this.tail=null};t.prototype={add:function(e){var t={item:e,next:null},i=this.tail;i?i.next=t:this.head=t,this.tail=t},get:function(){var e=this.head;if(e)return null===(this.head=e.next)&&(this.tail=null),e.item}},e.exports=t},9645:function(e,t,i){"use strict";var n=i(4214),r=TypeError;e.exports=function(e){if(n(e))throw new r("Can't call method on "+e);return e}},6028:function(e,t,i){"use strict";var n=i(8168),r=i(7893),s=Object.getOwnPropertyDescriptor;e.exports=function(e){if(!r)return n[e];var t=s(n,e);return t&&t.value}},7723:function(e,t,i){"use strict";var n,r=i(8168),s=i(8974),o=i(3204),a=i(1162),c=i(2917),l=i(8137),d=i(541),u=r.Function,h=/MSIE .\./.test(c)||a&&((n=r.Bun.version.split(".")).length<3||"0"===n[0]&&(n[1]<3||"3"===n[1]&&"0"===n[2]));e.exports=function(e,t){var i=t?2:1;return h?function(n,r){var a=d(arguments.length,1)>i,c=o(n)?n:u(n),h=a?l(arguments,i):[],g=a?function(){s(c,this,h)}:c;return t?e(g,r):e(g)}:e}},6532:function(e,t,i){"use strict";var n=i(9660),r=i(1325),s=i(7602),o=i(7893),a=s("species");e.exports=function(e){var t=n(e);o&&t&&!t[a]&&r(t,a,{configurable:!0,get:function(){return this}})}},4018:function(e,t,i){"use strict";var n=i(1769),r=i(4154).f,s=i(7872),o=i(5674),a=i(1708),c=i(7602)("toStringTag");e.exports=function(e,t,i,l){var d=i?e:e&&e.prototype;d&&(o(d,c)||r(d,c,{configurable:!0,value:t}),l&&!n&&s(d,"toString",a))}},7552:function(e,t,i){"use strict";var n=i(1506),r=i(6665),s=n("keys");e.exports=function(e){return s[e]||(s[e]=r(e))}},7150:function(e,t,i){"use strict";var n=i(8168),r=i(1638),s="__core-js_shared__",o=n[s]||r(s,{});e.exports=o},1506:function(e,t,i){"use strict";var n=i(670),r=i(7150);(e.exports=function(e,t){return r[e]||(r[e]=void 0!==t?t:{})})("versions",[]).push({version:"3.35.0",mode:n?"pure":"global",copyright:"© 2014-2023 Denis Pushkarev (zloirock.ru)",license:"https://github.com/zloirock/core-js/blob/v3.35.0/LICENSE",source:"https://github.com/zloirock/core-js"})},3607:function(e,t,i){"use strict";var n=i(6802),r=i(5897),s=i(4214),o=i(7602)("species");e.exports=function(e,t){var i,a=n(e).constructor;return void 0===a||s(i=n(a)[o])?t:r(i)}},3372:function(e,t,i){"use strict";var n=i(5577),r=i(9632),s=i(9618),o=i(9645),a=n("".charAt),c=n("".charCodeAt),l=n("".slice),d=function(e){return function(t,i){var n,d,u=s(o(t)),h=r(i),g=u.length;return h<0||h>=g?e?"":void 0:(n=c(u,h))<55296||n>56319||h+1===g||(d=c(u,h+1))<56320||d>57343?e?a(u,h):n:e?l(u,h,h+2):d-56320+(n-55296<<10)+65536}};e.exports={codeAt:d(!1),charAt:d(!0)}},8782:function(e,t,i){"use strict";var n=i(5577),r=2147483647,s=/[^\0-\u007E]/,o=/[.\u3002\uFF0E\uFF61]/g,a="Overflow: input needs wider integers to process",c=RangeError,l=n(o.exec),d=Math.floor,u=String.fromCharCode,h=n("".charCodeAt),g=n([].join),f=n([].push),p=n("".replace),v=n("".split),b=n("".toLowerCase),m=function(e){return e+22+75*(e<26)},y=function(e,t,i){var n=0;for(e=i?d(e/700):e>>1,e+=d(e/t);e>455;)e=d(e/35),n+=36;return d(n+36*e/(e+38))},w=function(e){var t=[];e=function(e){for(var t=[],i=0,n=e.length;i<n;){var r=h(e,i++);if(r>=55296&&r<=56319&&i<n){var s=h(e,i++);56320==(64512&s)?f(t,((1023&r)<<10)+(1023&s)+65536):(f(t,r),i--)}else f(t,r)}return t}(e);var i,n,s=e.length,o=128,l=0,p=72;for(i=0;i<e.length;i++)(n=e[i])<128&&f(t,u(n));var v=t.length,b=v;for(v&&f(t,"-");b<s;){var w=r;for(i=0;i<e.length;i++)(n=e[i])>=o&&n<w&&(w=n);var x=b+1;if(w-o>d((r-l)/x))throw new c(a);for(l+=(w-o)*x,o=w,i=0;i<e.length;i++){if((n=e[i])<o&&++l>r)throw new c(a);if(n===o){for(var k=l,A=36;;){var S=A<=p?1:A>=p+26?26:A-p;if(k<S)break;var C=k-S,T=36-S;f(t,u(m(S+C%T))),k=d(C/T),A+=36}f(t,u(m(k))),p=y(l,x,b===v),l=0,b++}}l++,o++}return g(t,"")};e.exports=function(e){var t,i,n=[],r=v(p(b(e),o,"."),".");for(t=0;t<r.length;t++)i=r[t],f(n,l(s,i)?"xn--"+w(i):i);return g(n,".")}},881:function(e,t,i){"use strict";var n=i(6519).PROPER,r=i(6986),s=i(369);e.exports=function(e){return r((function(){return!!s[e]()||"​᠎"!=="​᠎"[e]()||n&&s[e].name!==e}))}},11:function(e,t,i){"use strict";var n=i(5577),r=i(9645),s=i(9618),o=i(369),a=n("".replace),c=RegExp("^["+o+"]+"),l=RegExp("(^|[^"+o+"])["+o+"]+$"),d=function(e){return function(t){var i=s(r(t));return 1&e&&(i=a(i,c,"")),2&e&&(i=a(i,l,"$1")),i}};e.exports={start:d(1),end:d(2),trim:d(3)}},952:function(e,t,i){"use strict";var n=i(9933),r=i(6986),s=i(8168).String;e.exports=!!Object.getOwnPropertySymbols&&!r((function(){var e=Symbol("symbol detection");return!s(e)||!(Object(e)instanceof Symbol)||!Symbol.sham&&n&&n<41}))},5050:function(e,t,i){"use strict";var n,r,s,o,a=i(8168),c=i(8974),l=i(5109),d=i(3204),u=i(5674),h=i(6986),g=i(1322),f=i(8137),p=i(766),v=i(541),b=i(1730),m=i(3271),y=a.setImmediate,w=a.clearImmediate,x=a.process,k=a.Dispatch,A=a.Function,S=a.MessageChannel,C=a.String,T=0,O={},I="onreadystatechange";h((function(){n=a.location}));var E=function(e){if(u(O,e)){var t=O[e];delete O[e],t()}},R=function(e){return function(){E(e)}},P=function(e){E(e.data)},$=function(e){a.postMessage(C(e),n.protocol+"//"+n.host)};y&&w||(y=function(e){v(arguments.length,1);var t=d(e)?e:A(e),i=f(arguments,1);return O[++T]=function(){c(t,void 0,i)},r(T),T},w=function(e){delete O[e]},m?r=function(e){x.nextTick(R(e))}:k&&k.now?r=function(e){k.now(R(e))}:S&&!b?(o=(s=new S).port2,s.port1.onmessage=P,r=l(o.postMessage,o)):a.addEventListener&&d(a.postMessage)&&!a.importScripts&&n&&"file:"!==n.protocol&&!h($)?(r=$,a.addEventListener("message",P,!1)):r=I in p("script")?function(e){g.appendChild(p("script"))[I]=function(){g.removeChild(this),E(e)}}:function(e){setTimeout(R(e),0)}),e.exports={set:y,clear:w}},8331:function(e,t,i){"use strict";var n=i(9632),r=Math.max,s=Math.min;e.exports=function(e,t){var i=n(e);return i<0?r(i+t,0):s(i,t)}},6724:function(e,t,i){"use strict";var n=i(1832),r=i(9645);e.exports=function(e){return n(r(e))}},9632:function(e,t,i){"use strict";var n=i(9718);e.exports=function(e){var t=+e;return t!=t||0===t?0:n(t)}},3315:function(e,t,i){"use strict";var n=i(9632),r=Math.min;e.exports=function(e){return e>0?r(n(e),9007199254740991):0}},68:function(e,t,i){"use strict";var n=i(9645),r=Object;e.exports=function(e){return r(n(e))}},4874:function(e,t,i){"use strict";var n=i(400),r=i(3367),s=i(7560),o=i(7545),a=i(6679),c=i(7602),l=TypeError,d=c("toPrimitive");e.exports=function(e,t){if(!r(e)||s(e))return e;var i,c=o(e,d);if(c){if(void 0===t&&(t="default"),i=n(c,e,t),!r(i)||s(i))return i;throw new l("Can't convert object to primitive value")}return void 0===t&&(t="number"),a(e,t)}},9248:function(e,t,i){"use strict";var n=i(4874),r=i(7560);e.exports=function(e){var t=n(e,"string");return r(t)?t:t+""}},1769:function(e,t,i){"use strict";var n={};n[i(7602)("toStringTag")]="z",e.exports="[object z]"===String(n)},9618:function(e,t,i){"use strict";var n=i(3238),r=String;e.exports=function(e){if("Symbol"===n(e))throw new TypeError("Cannot convert a Symbol value to a string");return r(e)}},9374:function(e){"use strict";var t=String;e.exports=function(e){try{return t(e)}catch(e){return"Object"}}},6665:function(e,t,i){"use strict";var n=i(5577),r=0,s=Math.random(),o=n(1..toString);e.exports=function(e){return"Symbol("+(void 0===e?"":e)+")_"+o(++r+s,36)}},2069:function(e,t,i){"use strict";var n=i(6986),r=i(7602),s=i(7893),o=i(670),a=r("iterator");e.exports=!n((function(){var e=new URL("b?a=1&b=2&c=3","http://a"),t=e.searchParams,i=new URLSearchParams("a=1&a=2&b=3"),n="";return e.pathname="c%20d",t.forEach((function(e,i){t.delete("b"),n+=i+e})),i.delete("a",2),i.delete("b",void 0),o&&(!e.toJSON||!i.has("a",1)||i.has("a",2)||!i.has("a",void 0)||i.has("b"))||!t.size&&(o||!s)||!t.sort||"http://a/c%20d?a=1&c=3"!==e.href||"3"!==t.get("c")||"a=1"!==String(new URLSearchParams("?a=1"))||!t[a]||"a"!==new URL("https://a@b").username||"b"!==new URLSearchParams(new URLSearchParams("a=b")).get("a")||"xn--e1aybc"!==new URL("http://тест").host||"#%D0%B1"!==new URL("http://a#б").hash||"a1c3"!==n||"x"!==new URL("http://x",void 0).host}))},8425:function(e,t,i){"use strict";var n=i(952);e.exports=n&&!Symbol.sham&&"symbol"==typeof Symbol.iterator},4603:function(e,t,i){"use strict";var n=i(7893),r=i(6986);e.exports=n&&r((function(){return 42!==Object.defineProperty((function(){}),"prototype",{value:42,writable:!1}).prototype}))},541:function(e){"use strict";var t=TypeError;e.exports=function(e,i){if(e<i)throw new t("Not enough arguments");return e}},8993:function(e,t,i){"use strict";var n=i(8168),r=i(3204),s=n.WeakMap;e.exports=r(s)&&/native code/.test(String(s))},7602:function(e,t,i){"use strict";var n=i(8168),r=i(1506),s=i(5674),o=i(6665),a=i(952),c=i(8425),l=n.Symbol,d=r("wks"),u=c?l.for||l:l&&l.withoutSetter||o;e.exports=function(e){return s(d,e)||(d[e]=a&&s(l,e)?l[e]:u("Symbol."+e)),d[e]}},369:function(e){"use strict";e.exports="\t\n\v\f\r                　\u2028\u2029\ufeff"},9870:function(e,t,i){"use strict";var n=i(437),r=i(5354),s=i(6866),o=i(3718),a=i(4361),c=i(3921),l=i(7872),d=i(5723),u=i(7113),h=i(2206),g=i(9889),f=i(3586),p=i(7602)("toStringTag"),v=Error,b=[].push,m=function(e,t){var i,n=r(y,this);o?i=o(new v,n?s(this):y):(i=n?this:c(y),l(i,p,"Error")),void 0!==t&&l(i,"message",f(t)),h(i,m,i.stack,1),arguments.length>2&&u(i,arguments[2]);var a=[];return g(e,b,{that:a}),l(i,"errors",a),i};o?o(m,v):a(m,v,{name:!0});var y=m.prototype=c(v.prototype,{constructor:d(1,m),message:d(1,""),name:d(1,"AggregateError")});n({global:!0,constructor:!0,arity:2},{AggregateError:m})},5184:function(e,t,i){"use strict";i(9870)},1948:function(e,t,i){"use strict";var n=i(437),r=i(6676);n({target:"Array",proto:!0,forced:[].forEach!==r},{forEach:r})},9819:function(e,t,i){"use strict";var n=i(437),r=i(4275);n({target:"Array",stat:!0,forced:!i(4075)((function(e){Array.from(e)}))},{from:r})},738:function(e,t,i){"use strict";var n=i(437),r=i(4634).includes,s=i(6986),o=i(9002);n({target:"Array",proto:!0,forced:s((function(){return!Array(1).includes()}))},{includes:function(e){return r(this,e,arguments.length>1?arguments[1]:void 0)}}),o("includes")},4509:function(e,t,i){"use strict";var n=i(437),r=i(8355),s=i(4634).indexOf,o=i(3165),a=r([].indexOf),c=!!a&&1/a([1],1,-0)<0;n({target:"Array",proto:!0,forced:c||!o("indexOf")},{indexOf:function(e){var t=arguments.length>1?arguments[1]:void 0;return c?a(this,e,t)||0:s(this,e,t)}})},9263:function(e,t,i){"use strict";i(437)({target:"Array",stat:!0},{isArray:i(1911)})},4089:function(e,t,i){"use strict";var n=i(6724),r=i(9002),s=i(5988),o=i(5126),a=i(4154).f,c=i(9945),l=i(9880),d=i(670),u=i(7893),h="Array Iterator",g=o.set,f=o.getterFor(h);e.exports=c(Array,"Array",(function(e,t){g(this,{type:h,target:n(e),index:0,kind:t})}),(function(){var e=f(this),t=e.target,i=e.index++;if(!t||i>=t.length)return e.target=void 0,l(void 0,!0);switch(e.kind){case"keys":return l(i,!1);case"values":return l(t[i],!1)}return l([i,t[i]],!1)}),"values");var p=s.Arguments=s.Array;if(r("keys"),r("values"),r("entries"),!d&&u&&"values"!==p.name)try{a(p,"name",{value:"values"})}catch(e){}},8429:function(e,t,i){"use strict";var n=i(437),r=i(1024).map;n({target:"Array",proto:!0,forced:!i(1794)("map")},{map:function(e){return r(this,e,arguments.length>1?arguments[1]:void 0)}})},8683:function(e,t,i){"use strict";var n=i(437),r=i(68),s=i(8331),o=i(9632),a=i(8949),c=i(6216),l=i(7418),d=i(6),u=i(313),h=i(2065),g=i(1794)("splice"),f=Math.max,p=Math.min;n({target:"Array",proto:!0,forced:!g},{splice:function(e,t){var i,n,g,v,b,m,y=r(this),w=a(y),x=s(e,w),k=arguments.length;for(0===k?i=n=0:1===k?(i=0,n=w-x):(i=k-2,n=p(f(o(t),0),w-x)),l(w+i-n),g=d(y,n),v=0;v<n;v++)(b=x+v)in y&&u(g,v,y[b]);if(g.length=n,i<n){for(v=x;v<w-n;v++)m=v+i,(b=v+n)in y?y[m]=y[b]:h(y,m);for(v=w;v>w-n+i;v--)h(y,v-1)}else if(i>n)for(v=w-n;v>x;v--)m=v+i-1,(b=v+n-1)in y?y[m]=y[b]:h(y,m);for(v=0;v<i;v++)y[v+x]=arguments[v+2];return c(y,w-n+i),g}})},6056:function(e,t,i){"use strict";var n=i(437),r=i(5577),s=Date,o=r(s.prototype.getTime);n({target:"Date",stat:!0},{now:function(){return o(new s)}})},8845:function(e,t,i){"use strict";var n=i(437),r=i(2843);n({target:"Function",proto:!0,forced:Function.bind!==r},{bind:r})},1087:function(e,t,i){"use strict";var n=i(437),r=i(9660),s=i(8974),o=i(400),a=i(5577),c=i(6986),l=i(3204),d=i(7560),u=i(8137),h=i(3334),g=i(952),f=String,p=r("JSON","stringify"),v=a(/./.exec),b=a("".charAt),m=a("".charCodeAt),y=a("".replace),w=a(1..toString),x=/[\uD800-\uDFFF]/g,k=/^[\uD800-\uDBFF]$/,A=/^[\uDC00-\uDFFF]$/,S=!g||c((function(){var e=r("Symbol")("stringify detection");return"[null]"!==p([e])||"{}"!==p({a:e})||"{}"!==p(Object(e))})),C=c((function(){return'"\\udf06\\ud834"'!==p("\udf06\ud834")||'"\\udead"'!==p("\udead")})),T=function(e,t){var i=u(arguments),n=h(t);if(l(n)||void 0!==e&&!d(e))return i[1]=function(e,t){if(l(n)&&(t=o(n,this,f(e),t)),!d(t))return t},s(p,null,i)},O=function(e,t,i){var n=b(i,t-1),r=b(i,t+1);return v(k,e)&&!v(A,r)||v(A,e)&&!v(k,n)?"\\u"+w(m(e,0),16):e};p&&n({target:"JSON",stat:!0,arity:3,forced:S||C},{stringify:function(e,t,i){var n=u(arguments),r=s(S?T:p,null,n);return C&&"string"==typeof r?y(r,x,O):r}})},9446:function(e,t,i){"use strict";i(437)({target:"Number",stat:!0},{isInteger:i(4648)})},2597:function(e,t,i){"use strict";i(437)({target:"Number",stat:!0},{isNaN:function(e){return e!=e}})},3115:function(e,t,i){"use strict";var n=i(437),r=i(68),s=i(6889);n({target:"Object",stat:!0,forced:i(6986)((function(){s(1)}))},{keys:function(e){return s(r(e))}})},3070:function(){},1160:function(e,t,i){"use strict";var n=i(437),r=i(8459);n({global:!0,forced:parseFloat!==r},{parseFloat:r})},3559:function(e,t,i){"use strict";var n=i(437),r=i(668);n({global:!0,forced:parseInt!==r},{parseInt:r})},4072:function(e,t,i){"use strict";var n=i(437),r=i(400),s=i(6377),o=i(2668),a=i(1618),c=i(9889);n({target:"Promise",stat:!0,forced:i(3948)},{allSettled:function(e){var t=this,i=o.f(t),n=i.resolve,l=i.reject,d=a((function(){var i=s(t.resolve),o=[],a=0,l=1;c(e,(function(e){var s=a++,c=!1;l++,r(i,t,e).then((function(e){c||(c=!0,o[s]={status:"fulfilled",value:e},--l||n(o))}),(function(e){c||(c=!0,o[s]={status:"rejected",reason:e},--l||n(o))}))})),--l||n(o)}));return d.error&&l(d.value),i.promise}})},6192:function(e,t,i){"use strict";var n=i(437),r=i(400),s=i(6377),o=i(2668),a=i(1618),c=i(9889);n({target:"Promise",stat:!0,forced:i(3948)},{all:function(e){var t=this,i=o.f(t),n=i.resolve,l=i.reject,d=a((function(){var i=s(t.resolve),o=[],a=0,d=1;c(e,(function(e){var s=a++,c=!1;d++,r(i,t,e).then((function(e){c||(c=!0,o[s]=e,--d||n(o))}),l)})),--d||n(o)}));return d.error&&l(d.value),i.promise}})},7021:function(e,t,i){"use strict";var n=i(437),r=i(400),s=i(6377),o=i(9660),a=i(2668),c=i(1618),l=i(9889),d=i(3948),u="No one promise resolved";n({target:"Promise",stat:!0,forced:d},{any:function(e){var t=this,i=o("AggregateError"),n=a.f(t),d=n.resolve,h=n.reject,g=c((function(){var n=s(t.resolve),o=[],a=0,c=1,g=!1;l(e,(function(e){var s=a++,l=!1;c++,r(n,t,e).then((function(e){l||g||(g=!0,d(e))}),(function(e){l||g||(l=!0,o[s]=e,--c||h(new i(o,u)))}))})),--c||h(new i(o,u))}));return g.error&&h(g.value),n.promise}})},9284:function(e,t,i){"use strict";var n=i(437),r=i(670),s=i(5741).CONSTRUCTOR,o=i(1437),a=i(9660),c=i(3204),l=i(8381),d=o&&o.prototype;if(n({target:"Promise",proto:!0,forced:s,real:!0},{catch:function(e){return this.then(void 0,e)}}),!r&&c(o)){var u=a("Promise").prototype.catch;d.catch!==u&&l(d,"catch",u,{unsafe:!0})}},1667:function(e,t,i){"use strict";var n,r,s,o=i(437),a=i(670),c=i(3271),l=i(8168),d=i(400),u=i(8381),h=i(3718),g=i(4018),f=i(6532),p=i(6377),v=i(3204),b=i(3367),m=i(3366),y=i(3607),w=i(5050).set,x=i(4726),k=i(1442),A=i(1618),S=i(9264),C=i(5126),T=i(1437),O=i(5741),I=i(2668),E="Promise",R=O.CONSTRUCTOR,P=O.REJECTION_EVENT,$=O.SUBCLASSING,L=C.getterFor(E),z=C.set,F=T&&T.prototype,U=T,B=F,N=l.TypeError,j=l.document,M=l.process,H=I.f,D=H,_=!!(j&&j.createEvent&&l.dispatchEvent),V="unhandledrejection",W=function(e){var t;return!(!b(e)||!v(t=e.then))&&t},q=function(e,t){var i,n,r,s=t.value,o=1===t.state,a=o?e.ok:e.fail,c=e.resolve,l=e.reject,u=e.domain;try{a?(o||(2===t.rejection&&J(t),t.rejection=1),!0===a?i=s:(u&&u.enter(),i=a(s),u&&(u.exit(),r=!0)),i===e.promise?l(new N("Promise-chain cycle")):(n=W(i))?d(n,i,c,l):c(i)):l(s)}catch(e){u&&!r&&u.exit(),l(e)}},G=function(e,t){e.notified||(e.notified=!0,x((function(){for(var i,n=e.reactions;i=n.get();)q(i,e);e.notified=!1,t&&!e.rejection&&Q(e)})))},Z=function(e,t,i){var n,r;_?((n=j.createEvent("Event")).promise=t,n.reason=i,n.initEvent(e,!1,!0),l.dispatchEvent(n)):n={promise:t,reason:i},!P&&(r=l["on"+e])?r(n):e===V&&k("Unhandled promise rejection",i)},Q=function(e){d(w,l,(function(){var t,i=e.facade,n=e.value;if(K(e)&&(t=A((function(){c?M.emit("unhandledRejection",n,i):Z(V,i,n)})),e.rejection=c||K(e)?2:1,t.error))throw t.value}))},K=function(e){return 1!==e.rejection&&!e.parent},J=function(e){d(w,l,(function(){var t=e.facade;c?M.emit("rejectionHandled",t):Z("rejectionhandled",t,e.value)}))},Y=function(e,t,i){return function(n){e(t,n,i)}},X=function(e,t,i){e.done||(e.done=!0,i&&(e=i),e.value=t,e.state=2,G(e,!0))},ee=function(e,t,i){if(!e.done){e.done=!0,i&&(e=i);try{if(e.facade===t)throw new N("Promise can't be resolved itself");var n=W(t);n?x((function(){var i={done:!1};try{d(n,t,Y(ee,i,e),Y(X,i,e))}catch(t){X(i,t,e)}})):(e.value=t,e.state=1,G(e,!1))}catch(t){X({done:!1},t,e)}}};if(R&&(B=(U=function(e){m(this,B),p(e),d(n,this);var t=L(this);try{e(Y(ee,t),Y(X,t))}catch(e){X(t,e)}}).prototype,(n=function(e){z(this,{type:E,done:!1,notified:!1,parent:!1,reactions:new S,rejection:!1,state:0,value:void 0})}).prototype=u(B,"then",(function(e,t){var i=L(this),n=H(y(this,U));return i.parent=!0,n.ok=!v(e)||e,n.fail=v(t)&&t,n.domain=c?M.domain:void 0,0===i.state?i.reactions.add(n):x((function(){q(n,i)})),n.promise})),r=function(){var e=new n,t=L(e);this.promise=e,this.resolve=Y(ee,t),this.reject=Y(X,t)},I.f=H=function(e){return e===U||void 0===e?new r(e):D(e)},!a&&v(T)&&F!==Object.prototype)){s=F.then,$||u(F,"then",(function(e,t){var i=this;return new U((function(e,t){d(s,i,e,t)})).then(e,t)}),{unsafe:!0});try{delete F.constructor}catch(e){}h&&h(F,B)}o({global:!0,constructor:!0,wrap:!0,forced:R},{Promise:U}),g(U,E,!1,!0),f(E)},9412:function(e,t,i){"use strict";var n=i(437),r=i(670),s=i(1437),o=i(6986),a=i(9660),c=i(3204),l=i(3607),d=i(1083),u=i(8381),h=s&&s.prototype;if(n({target:"Promise",proto:!0,real:!0,forced:!!s&&o((function(){h.finally.call({then:function(){}},(function(){}))}))},{finally:function(e){var t=l(this,a("Promise")),i=c(e);return this.then(i?function(i){return d(t,e()).then((function(){return i}))}:e,i?function(i){return d(t,e()).then((function(){throw i}))}:e)}}),!r&&c(s)){var g=a("Promise").prototype.finally;h.finally!==g&&u(h,"finally",g,{unsafe:!0})}},9113:function(e,t,i){"use strict";i(1667),i(6192),i(9284),i(2622),i(9920),i(6067)},2622:function(e,t,i){"use strict";var n=i(437),r=i(400),s=i(6377),o=i(2668),a=i(1618),c=i(9889);n({target:"Promise",stat:!0,forced:i(3948)},{race:function(e){var t=this,i=o.f(t),n=i.reject,l=a((function(){var o=s(t.resolve);c(e,(function(e){r(o,t,e).then(i.resolve,n)}))}));return l.error&&n(l.value),i.promise}})},9920:function(e,t,i){"use strict";var n=i(437),r=i(2668);n({target:"Promise",stat:!0,forced:i(5741).CONSTRUCTOR},{reject:function(e){var t=r.f(this);return(0,t.reject)(e),t.promise}})},6067:function(e,t,i){"use strict";var n=i(437),r=i(9660),s=i(670),o=i(1437),a=i(5741).CONSTRUCTOR,c=i(1083),l=r("Promise"),d=s&&!a;n({target:"Promise",stat:!0,forced:s||a},{resolve:function(e){return c(d&&this===l?o:this,e)}})},6849:function(e,t,i){"use strict";var n=i(437),r=i(2668);n({target:"Promise",stat:!0},{withResolvers:function(){var e=r.f(this);return{promise:e.promise,resolve:e.resolve,reject:e.reject}}})},8002:function(e,t,i){"use strict";i(2711)("Set",(function(e){return function(){return e(this,arguments.length?arguments[0]:void 0)}}),i(8119))},3116:function(e,t,i){"use strict";i(8002)},716:function(e,t,i){"use strict";var n=i(437),r=i(5577),s=i(156),o=i(9645),a=i(9618),c=i(1313),l=r("".indexOf);n({target:"String",proto:!0,forced:!c("includes")},{includes:function(e){return!!~l(a(o(this)),a(s(e)),arguments.length>1?arguments[1]:void 0)}})},3131:function(e,t,i){"use strict";var n=i(3372).charAt,r=i(9618),s=i(5126),o=i(9945),a=i(9880),c="String Iterator",l=s.set,d=s.getterFor(c);o(String,"String",(function(e){l(this,{type:c,string:r(e),index:0})}),(function(){var e,t=d(this),i=t.string,r=t.index;return r>=i.length?a(void 0,!0):(e=n(i,r),t.index+=e.length,a(e,!1))}))},2249:function(e,t,i){"use strict";var n=i(437),r=i(11).trim;n({target:"String",proto:!0,forced:i(881)("trim")},{trim:function(){return r(this)}})},9291:function(){},9594:function(e,t,i){"use strict";i(4089);var n=i(2765),r=i(8168),s=i(4018),o=i(5988);for(var a in n)s(r[a],a),o[a]=o.Array},9400:function(e,t,i){"use strict";var n=i(437),r=i(8168),s=i(7723)(r.setInterval,!0);n({global:!0,bind:!0,forced:r.setInterval!==s},{setInterval:s})},2938:function(e,t,i){"use strict";var n=i(437),r=i(8168),s=i(7723)(r.setTimeout,!0);n({global:!0,bind:!0,forced:r.setTimeout!==s},{setTimeout:s})},3332:function(e,t,i){"use strict";i(9400),i(2938)},7847:function(e,t,i){"use strict";i(4089);var n=i(437),r=i(8168),s=i(6028),o=i(400),a=i(5577),c=i(7893),l=i(2069),d=i(8381),u=i(1325),h=i(1576),g=i(4018),f=i(8287),p=i(5126),v=i(3366),b=i(3204),m=i(5674),y=i(5109),w=i(3238),x=i(6802),k=i(3367),A=i(9618),S=i(3921),C=i(5723),T=i(2374),O=i(7994),I=i(9880),E=i(541),R=i(7602),P=i(1399),$=R("iterator"),L="URLSearchParams",z=L+"Iterator",F=p.set,U=p.getterFor(L),B=p.getterFor(z),N=s("fetch"),j=s("Request"),M=s("Headers"),H=j&&j.prototype,D=M&&M.prototype,_=r.RegExp,V=r.TypeError,W=r.decodeURIComponent,q=r.encodeURIComponent,G=a("".charAt),Z=a([].join),Q=a([].push),K=a("".replace),J=a([].shift),Y=a([].splice),X=a("".split),ee=a("".slice),te=/\+/g,ie=Array(4),ne=function(e){return ie[e-1]||(ie[e-1]=_("((?:%[\\da-f]{2}){"+e+"})","gi"))},re=function(e){try{return W(e)}catch(t){return e}},se=function(e){var t=K(e,te," "),i=4;try{return W(t)}catch(e){for(;i;)t=K(t,ne(i--),re);return t}},oe=/[!'()~]|%20/g,ae={"!":"%21","'":"%27","(":"%28",")":"%29","~":"%7E","%20":"+"},ce=function(e){return ae[e]},le=function(e){return K(q(e),oe,ce)},de=f((function(e,t){F(this,{type:z,target:U(e).entries,index:0,kind:t})}),L,(function(){var e=B(this),t=e.target,i=e.index++;if(!t||i>=t.length)return e.target=void 0,I(void 0,!0);var n=t[i];switch(e.kind){case"keys":return I(n.key,!1);case"values":return I(n.value,!1)}return I([n.key,n.value],!1)}),!0),ue=function(e){this.entries=[],this.url=null,void 0!==e&&(k(e)?this.parseObject(e):this.parseQuery("string"==typeof e?"?"===G(e,0)?ee(e,1):e:A(e)))};ue.prototype={type:L,bindURL:function(e){this.url=e,this.update()},parseObject:function(e){var t,i,n,r,s,a,c,l=this.entries,d=O(e);if(d)for(i=(t=T(e,d)).next;!(n=o(i,t)).done;){if(s=(r=T(x(n.value))).next,(a=o(s,r)).done||(c=o(s,r)).done||!o(s,r).done)throw new V("Expected sequence with length 2");Q(l,{key:A(a.value),value:A(c.value)})}else for(var u in e)m(e,u)&&Q(l,{key:u,value:A(e[u])})},parseQuery:function(e){if(e)for(var t,i,n=this.entries,r=X(e,"&"),s=0;s<r.length;)(t=r[s++]).length&&(i=X(t,"="),Q(n,{key:se(J(i)),value:se(Z(i,"="))}))},serialize:function(){for(var e,t=this.entries,i=[],n=0;n<t.length;)e=t[n++],Q(i,le(e.key)+"="+le(e.value));return Z(i,"&")},update:function(){this.entries.length=0,this.parseQuery(this.url.query)},updateURL:function(){this.url&&this.url.update()}};var he=function(){v(this,ge);var e=F(this,new ue(arguments.length>0?arguments[0]:void 0));c||(this.size=e.entries.length)},ge=he.prototype;if(h(ge,{append:function(e,t){var i=U(this);E(arguments.length,2),Q(i.entries,{key:A(e),value:A(t)}),c||this.length++,i.updateURL()},delete:function(e){for(var t=U(this),i=E(arguments.length,1),n=t.entries,r=A(e),s=i<2?void 0:arguments[1],o=void 0===s?s:A(s),a=0;a<n.length;){var l=n[a];if(l.key!==r||void 0!==o&&l.value!==o)a++;else if(Y(n,a,1),void 0!==o)break}c||(this.size=n.length),t.updateURL()},get:function(e){var t=U(this).entries;E(arguments.length,1);for(var i=A(e),n=0;n<t.length;n++)if(t[n].key===i)return t[n].value;return null},getAll:function(e){var t=U(this).entries;E(arguments.length,1);for(var i=A(e),n=[],r=0;r<t.length;r++)t[r].key===i&&Q(n,t[r].value);return n},has:function(e){for(var t=U(this).entries,i=E(arguments.length,1),n=A(e),r=i<2?void 0:arguments[1],s=void 0===r?r:A(r),o=0;o<t.length;){var a=t[o++];if(a.key===n&&(void 0===s||a.value===s))return!0}return!1},set:function(e,t){var i=U(this);E(arguments.length,1);for(var n,r=i.entries,s=!1,o=A(e),a=A(t),l=0;l<r.length;l++)(n=r[l]).key===o&&(s?Y(r,l--,1):(s=!0,n.value=a));s||Q(r,{key:o,value:a}),c||(this.size=r.length),i.updateURL()},sort:function(){var e=U(this);P(e.entries,(function(e,t){return e.key>t.key?1:-1})),e.updateURL()},forEach:function(e){for(var t,i=U(this).entries,n=y(e,arguments.length>1?arguments[1]:void 0),r=0;r<i.length;)n((t=i[r++]).value,t.key,this)},keys:function(){return new de(this,"keys")},values:function(){return new de(this,"values")},entries:function(){return new de(this,"entries")}},{enumerable:!0}),d(ge,$,ge.entries,{name:"entries"}),d(ge,"toString",(function(){return U(this).serialize()}),{enumerable:!0}),c&&u(ge,"size",{get:function(){return U(this).entries.length},configurable:!0,enumerable:!0}),g(he,L),n({global:!0,constructor:!0,forced:!l},{URLSearchParams:he}),!l&&b(M)){var fe=a(D.has),pe=a(D.set),ve=function(e){if(k(e)){var t,i=e.body;if(w(i)===L)return t=e.headers?new M(e.headers):new M,fe(t,"content-type")||pe(t,"content-type","application/x-www-form-urlencoded;charset=UTF-8"),S(e,{body:C(0,A(i)),headers:C(0,t)})}return e};if(b(N)&&n({global:!0,enumerable:!0,dontCallGetSet:!0,forced:!0},{fetch:function(e){return N(e,arguments.length>1?ve(arguments[1]):{})}}),b(j)){var be=function(e){return v(this,H),new j(e,arguments.length>1?ve(arguments[1]):{})};H.constructor=be,be.prototype=H,n({global:!0,constructor:!0,dontCallGetSet:!0,forced:!0},{Request:be})}}e.exports={URLSearchParams:he,getState:U}},7596:function(){},1555:function(){},9573:function(e,t,i){"use strict";i(7847)},8150:function(){},199:function(e,t,i){"use strict";var n=i(437),r=i(9660),s=i(6986),o=i(541),a=i(9618),c=i(2069),l=r("URL");n({target:"URL",stat:!0,forced:!(c&&s((function(){l.canParse()})))},{canParse:function(e){var t=o(arguments.length,1),i=a(e),n=t<2||void 0===arguments[1]?void 0:a(arguments[1]);try{return!!new l(i,n)}catch(e){return!1}}})},7223:function(e,t,i){"use strict";i(3131);var n,r=i(437),s=i(7893),o=i(2069),a=i(8168),c=i(5109),l=i(5577),d=i(8381),u=i(1325),h=i(3366),g=i(5674),f=i(2872),p=i(4275),v=i(8137),b=i(3372).codeAt,m=i(8782),y=i(9618),w=i(4018),x=i(541),k=i(7847),A=i(5126),S=A.set,C=A.getterFor("URL"),T=k.URLSearchParams,O=k.getState,I=a.URL,E=a.TypeError,R=a.parseInt,P=Math.floor,$=Math.pow,L=l("".charAt),z=l(/./.exec),F=l([].join),U=l(1..toString),B=l([].pop),N=l([].push),j=l("".replace),M=l([].shift),H=l("".split),D=l("".slice),_=l("".toLowerCase),V=l([].unshift),W="Invalid scheme",q="Invalid host",G="Invalid port",Z=/[a-z]/i,Q=/[\d+-.a-z]/i,K=/\d/,J=/^0x/i,Y=/^[0-7]+$/,X=/^\d+$/,ee=/^[\da-f]+$/i,te=/[\0\t\n\r #%/:<>?@[\\\]^|]/,ie=/[\0\t\n\r #/:<>?@[\\\]^|]/,ne=/^[\u0000-\u0020]+/,re=/(^|[^\u0000-\u0020])[\u0000-\u0020]+$/,se=/[\t\n\r]/g,oe=function(e){var t,i,n,r;if("number"==typeof e){for(t=[],i=0;i<4;i++)V(t,e%256),e=P(e/256);return F(t,".")}if("object"==typeof e){for(t="",n=function(e){for(var t=null,i=1,n=null,r=0,s=0;s<8;s++)0!==e[s]?(r>i&&(t=n,i=r),n=null,r=0):(null===n&&(n=s),++r);return r>i&&(t=n,i=r),t}(e),i=0;i<8;i++)r&&0===e[i]||(r&&(r=!1),n===i?(t+=i?":":"::",r=!0):(t+=U(e[i],16),i<7&&(t+=":")));return"["+t+"]"}return e},ae={},ce=f({},ae,{" ":1,'"':1,"<":1,">":1,"`":1}),le=f({},ce,{"#":1,"?":1,"{":1,"}":1}),de=f({},le,{"/":1,":":1,";":1,"=":1,"@":1,"[":1,"\\":1,"]":1,"^":1,"|":1}),ue=function(e,t){var i=b(e,0);return i>32&&i<127&&!g(t,e)?e:encodeURIComponent(e)},he={ftp:21,file:null,http:80,https:443,ws:80,wss:443},ge=function(e,t){var i;return 2===e.length&&z(Z,L(e,0))&&(":"===(i=L(e,1))||!t&&"|"===i)},fe=function(e){var t;return e.length>1&&ge(D(e,0,2))&&(2===e.length||"/"===(t=L(e,2))||"\\"===t||"?"===t||"#"===t)},pe=function(e){return"."===e||"%2e"===_(e)},ve={},be={},me={},ye={},we={},xe={},ke={},Ae={},Se={},Ce={},Te={},Oe={},Ie={},Ee={},Re={},Pe={},$e={},Le={},ze={},Fe={},Ue={},Be=function(e,t,i){var n,r,s,o=y(e);if(t){if(r=this.parse(o))throw new E(r);this.searchParams=null}else{if(void 0!==i&&(n=new Be(i,!0)),r=this.parse(o,null,n))throw new E(r);(s=O(new T)).bindURL(this),this.searchParams=s}};Be.prototype={type:"URL",parse:function(e,t,i){var r,s,o,a,c,l=this,d=t||ve,u=0,h="",f=!1,b=!1,m=!1;for(e=y(e),t||(l.scheme="",l.username="",l.password="",l.host=null,l.port=null,l.path=[],l.query=null,l.fragment=null,l.cannotBeABaseURL=!1,e=j(e,ne,""),e=j(e,re,"$1")),e=j(e,se,""),r=p(e);u<=r.length;){switch(s=r[u],d){case ve:if(!s||!z(Z,s)){if(t)return W;d=me;continue}h+=_(s),d=be;break;case be:if(s&&(z(Q,s)||"+"===s||"-"===s||"."===s))h+=_(s);else{if(":"!==s){if(t)return W;h="",d=me,u=0;continue}if(t&&(l.isSpecial()!==g(he,h)||"file"===h&&(l.includesCredentials()||null!==l.port)||"file"===l.scheme&&!l.host))return;if(l.scheme=h,t)return void(l.isSpecial()&&he[l.scheme]===l.port&&(l.port=null));h="","file"===l.scheme?d=Ee:l.isSpecial()&&i&&i.scheme===l.scheme?d=ye:l.isSpecial()?d=Ae:"/"===r[u+1]?(d=we,u++):(l.cannotBeABaseURL=!0,N(l.path,""),d=ze)}break;case me:if(!i||i.cannotBeABaseURL&&"#"!==s)return W;if(i.cannotBeABaseURL&&"#"===s){l.scheme=i.scheme,l.path=v(i.path),l.query=i.query,l.fragment="",l.cannotBeABaseURL=!0,d=Ue;break}d="file"===i.scheme?Ee:xe;continue;case ye:if("/"!==s||"/"!==r[u+1]){d=xe;continue}d=Se,u++;break;case we:if("/"===s){d=Ce;break}d=Le;continue;case xe:if(l.scheme=i.scheme,s===n)l.username=i.username,l.password=i.password,l.host=i.host,l.port=i.port,l.path=v(i.path),l.query=i.query;else if("/"===s||"\\"===s&&l.isSpecial())d=ke;else if("?"===s)l.username=i.username,l.password=i.password,l.host=i.host,l.port=i.port,l.path=v(i.path),l.query="",d=Fe;else{if("#"!==s){l.username=i.username,l.password=i.password,l.host=i.host,l.port=i.port,l.path=v(i.path),l.path.length--,d=Le;continue}l.username=i.username,l.password=i.password,l.host=i.host,l.port=i.port,l.path=v(i.path),l.query=i.query,l.fragment="",d=Ue}break;case ke:if(!l.isSpecial()||"/"!==s&&"\\"!==s){if("/"!==s){l.username=i.username,l.password=i.password,l.host=i.host,l.port=i.port,d=Le;continue}d=Ce}else d=Se;break;case Ae:if(d=Se,"/"!==s||"/"!==L(h,u+1))continue;u++;break;case Se:if("/"!==s&&"\\"!==s){d=Ce;continue}break;case Ce:if("@"===s){f&&(h="%40"+h),f=!0,o=p(h);for(var w=0;w<o.length;w++){var x=o[w];if(":"!==x||m){var k=ue(x,de);m?l.password+=k:l.username+=k}else m=!0}h=""}else if(s===n||"/"===s||"?"===s||"#"===s||"\\"===s&&l.isSpecial()){if(f&&""===h)return"Invalid authority";u-=p(h).length+1,h="",d=Te}else h+=s;break;case Te:case Oe:if(t&&"file"===l.scheme){d=Pe;continue}if(":"!==s||b){if(s===n||"/"===s||"?"===s||"#"===s||"\\"===s&&l.isSpecial()){if(l.isSpecial()&&""===h)return q;if(t&&""===h&&(l.includesCredentials()||null!==l.port))return;if(a=l.parseHost(h))return a;if(h="",d=$e,t)return;continue}"["===s?b=!0:"]"===s&&(b=!1),h+=s}else{if(""===h)return q;if(a=l.parseHost(h))return a;if(h="",d=Ie,t===Oe)return}break;case Ie:if(!z(K,s)){if(s===n||"/"===s||"?"===s||"#"===s||"\\"===s&&l.isSpecial()||t){if(""!==h){var A=R(h,10);if(A>65535)return G;l.port=l.isSpecial()&&A===he[l.scheme]?null:A,h=""}if(t)return;d=$e;continue}return G}h+=s;break;case Ee:if(l.scheme="file","/"===s||"\\"===s)d=Re;else{if(!i||"file"!==i.scheme){d=Le;continue}switch(s){case n:l.host=i.host,l.path=v(i.path),l.query=i.query;break;case"?":l.host=i.host,l.path=v(i.path),l.query="",d=Fe;break;case"#":l.host=i.host,l.path=v(i.path),l.query=i.query,l.fragment="",d=Ue;break;default:fe(F(v(r,u),""))||(l.host=i.host,l.path=v(i.path),l.shortenPath()),d=Le;continue}}break;case Re:if("/"===s||"\\"===s){d=Pe;break}i&&"file"===i.scheme&&!fe(F(v(r,u),""))&&(ge(i.path[0],!0)?N(l.path,i.path[0]):l.host=i.host),d=Le;continue;case Pe:if(s===n||"/"===s||"\\"===s||"?"===s||"#"===s){if(!t&&ge(h))d=Le;else if(""===h){if(l.host="",t)return;d=$e}else{if(a=l.parseHost(h))return a;if("localhost"===l.host&&(l.host=""),t)return;h="",d=$e}continue}h+=s;break;case $e:if(l.isSpecial()){if(d=Le,"/"!==s&&"\\"!==s)continue}else if(t||"?"!==s)if(t||"#"!==s){if(s!==n&&(d=Le,"/"!==s))continue}else l.fragment="",d=Ue;else l.query="",d=Fe;break;case Le:if(s===n||"/"===s||"\\"===s&&l.isSpecial()||!t&&("?"===s||"#"===s)){if(".."===(c=_(c=h))||"%2e."===c||".%2e"===c||"%2e%2e"===c?(l.shortenPath(),"/"===s||"\\"===s&&l.isSpecial()||N(l.path,"")):pe(h)?"/"===s||"\\"===s&&l.isSpecial()||N(l.path,""):("file"===l.scheme&&!l.path.length&&ge(h)&&(l.host&&(l.host=""),h=L(h,0)+":"),N(l.path,h)),h="","file"===l.scheme&&(s===n||"?"===s||"#"===s))for(;l.path.length>1&&""===l.path[0];)M(l.path);"?"===s?(l.query="",d=Fe):"#"===s&&(l.fragment="",d=Ue)}else h+=ue(s,le);break;case ze:"?"===s?(l.query="",d=Fe):"#"===s?(l.fragment="",d=Ue):s!==n&&(l.path[0]+=ue(s,ae));break;case Fe:t||"#"!==s?s!==n&&("'"===s&&l.isSpecial()?l.query+="%27":l.query+="#"===s?"%23":ue(s,ae)):(l.fragment="",d=Ue);break;case Ue:s!==n&&(l.fragment+=ue(s,ce))}u++}},parseHost:function(e){var t,i,n;if("["===L(e,0)){if("]"!==L(e,e.length-1))return q;if(t=function(e){var t,i,n,r,s,o,a,c=[0,0,0,0,0,0,0,0],l=0,d=null,u=0,h=function(){return L(e,u)};if(":"===h()){if(":"!==L(e,1))return;u+=2,d=++l}for(;h();){if(8===l)return;if(":"!==h()){for(t=i=0;i<4&&z(ee,h());)t=16*t+R(h(),16),u++,i++;if("."===h()){if(0===i)return;if(u-=i,l>6)return;for(n=0;h();){if(r=null,n>0){if(!("."===h()&&n<4))return;u++}if(!z(K,h()))return;for(;z(K,h());){if(s=R(h(),10),null===r)r=s;else{if(0===r)return;r=10*r+s}if(r>255)return;u++}c[l]=256*c[l]+r,2!=++n&&4!==n||l++}if(4!==n)return;break}if(":"===h()){if(u++,!h())return}else if(h())return;c[l++]=t}else{if(null!==d)return;u++,d=++l}}if(null!==d)for(o=l-d,l=7;0!==l&&o>0;)a=c[l],c[l--]=c[d+o-1],c[d+--o]=a;else if(8!==l)return;return c}(D(e,1,-1)),!t)return q;this.host=t}else if(this.isSpecial()){if(e=m(e),z(te,e))return q;if(t=function(e){var t,i,n,r,s,o,a,c=H(e,".");if(c.length&&""===c[c.length-1]&&c.length--,(t=c.length)>4)return e;for(i=[],n=0;n<t;n++){if(""===(r=c[n]))return e;if(s=10,r.length>1&&"0"===L(r,0)&&(s=z(J,r)?16:8,r=D(r,8===s?1:2)),""===r)o=0;else{if(!z(10===s?X:8===s?Y:ee,r))return e;o=R(r,s)}N(i,o)}for(n=0;n<t;n++)if(o=i[n],n===t-1){if(o>=$(256,5-t))return null}else if(o>255)return null;for(a=B(i),n=0;n<i.length;n++)a+=i[n]*$(256,3-n);return a}(e),null===t)return q;this.host=t}else{if(z(ie,e))return q;for(t="",i=p(e),n=0;n<i.length;n++)t+=ue(i[n],ae);this.host=t}},cannotHaveUsernamePasswordPort:function(){return!this.host||this.cannotBeABaseURL||"file"===this.scheme},includesCredentials:function(){return""!==this.username||""!==this.password},isSpecial:function(){return g(he,this.scheme)},shortenPath:function(){var e=this.path,t=e.length;!t||"file"===this.scheme&&1===t&&ge(e[0],!0)||e.length--},serialize:function(){var e=this,t=e.scheme,i=e.username,n=e.password,r=e.host,s=e.port,o=e.path,a=e.query,c=e.fragment,l=t+":";return null!==r?(l+="//",e.includesCredentials()&&(l+=i+(n?":"+n:"")+"@"),l+=oe(r),null!==s&&(l+=":"+s)):"file"===t&&(l+="//"),l+=e.cannotBeABaseURL?o[0]:o.length?"/"+F(o,"/"):"",null!==a&&(l+="?"+a),null!==c&&(l+="#"+c),l},setHref:function(e){var t=this.parse(e);if(t)throw new E(t);this.searchParams.update()},getOrigin:function(){var e=this.scheme,t=this.port;if("blob"===e)try{return new Ne(e.path[0]).origin}catch(e){return"null"}return"file"!==e&&this.isSpecial()?e+"://"+oe(this.host)+(null!==t?":"+t:""):"null"},getProtocol:function(){return this.scheme+":"},setProtocol:function(e){this.parse(y(e)+":",ve)},getUsername:function(){return this.username},setUsername:function(e){var t=p(y(e));if(!this.cannotHaveUsernamePasswordPort()){this.username="";for(var i=0;i<t.length;i++)this.username+=ue(t[i],de)}},getPassword:function(){return this.password},setPassword:function(e){var t=p(y(e));if(!this.cannotHaveUsernamePasswordPort()){this.password="";for(var i=0;i<t.length;i++)this.password+=ue(t[i],de)}},getHost:function(){var e=this.host,t=this.port;return null===e?"":null===t?oe(e):oe(e)+":"+t},setHost:function(e){this.cannotBeABaseURL||this.parse(e,Te)},getHostname:function(){var e=this.host;return null===e?"":oe(e)},setHostname:function(e){this.cannotBeABaseURL||this.parse(e,Oe)},getPort:function(){var e=this.port;return null===e?"":y(e)},setPort:function(e){this.cannotHaveUsernamePasswordPort()||(""===(e=y(e))?this.port=null:this.parse(e,Ie))},getPathname:function(){var e=this.path;return this.cannotBeABaseURL?e[0]:e.length?"/"+F(e,"/"):""},setPathname:function(e){this.cannotBeABaseURL||(this.path=[],this.parse(e,$e))},getSearch:function(){var e=this.query;return e?"?"+e:""},setSearch:function(e){""===(e=y(e))?this.query=null:("?"===L(e,0)&&(e=D(e,1)),this.query="",this.parse(e,Fe)),this.searchParams.update()},getSearchParams:function(){return this.searchParams.facade},getHash:function(){var e=this.fragment;return e?"#"+e:""},setHash:function(e){""!==(e=y(e))?("#"===L(e,0)&&(e=D(e,1)),this.fragment="",this.parse(e,Ue)):this.fragment=null},update:function(){this.query=this.searchParams.serialize()||null}};var Ne=function(e){var t=h(this,je),i=x(arguments.length,1)>1?arguments[1]:void 0,n=S(t,new Be(e,!1,i));s||(t.href=n.serialize(),t.origin=n.getOrigin(),t.protocol=n.getProtocol(),t.username=n.getUsername(),t.password=n.getPassword(),t.host=n.getHost(),t.hostname=n.getHostname(),t.port=n.getPort(),t.pathname=n.getPathname(),t.search=n.getSearch(),t.searchParams=n.getSearchParams(),t.hash=n.getHash())},je=Ne.prototype,Me=function(e,t){return{get:function(){return C(this)[e]()},set:t&&function(e){return C(this)[t](e)},configurable:!0,enumerable:!0}};if(s&&(u(je,"href",Me("serialize","setHref")),u(je,"origin",Me("getOrigin")),u(je,"protocol",Me("getProtocol","setProtocol")),u(je,"username",Me("getUsername","setUsername")),u(je,"password",Me("getPassword","setPassword")),u(je,"host",Me("getHost","setHost")),u(je,"hostname",Me("getHostname","setHostname")),u(je,"port",Me("getPort","setPort")),u(je,"pathname",Me("getPathname","setPathname")),u(je,"search",Me("getSearch","setSearch")),u(je,"searchParams",Me("getSearchParams")),u(je,"hash",Me("getHash","setHash"))),d(je,"toJSON",(function(){return C(this).serialize()}),{enumerable:!0}),d(je,"toString",(function(){return C(this).serialize()}),{enumerable:!0}),I){var He=I.createObjectURL,De=I.revokeObjectURL;He&&d(Ne,"createObjectURL",c(He,I)),De&&d(Ne,"revokeObjectURL",c(De,I))}w(Ne,"URL"),r({global:!0,constructor:!0,forced:!o,sham:!s},{URL:Ne})},8069:function(e,t,i){"use strict";i(7223)},949:function(){},6104:function(e,t,i){"use strict";var n=i(353);e.exports=n},7392:function(e,t,i){"use strict";var n=i(3677);e.exports=n},926:function(e,t,i){"use strict";var n=i(2965);e.exports=n},1271:function(e,t,i){"use strict";var n=i(3638);e.exports=n},6201:function(e,t,i){"use strict";var n=i(1940);e.exports=n},899:function(e,t,i){"use strict";var n=i(5876);e.exports=n},2066:function(e,t,i){"use strict";i(9594);var n=i(3238),r=i(5674),s=i(5354),o=i(926),a=Array.prototype,c={DOMTokenList:!0,NodeList:!0};e.exports=function(e){var t=e.entries;return e===a||s(a,e)&&t===a.entries||r(c,n(e))?o:t}},1491:function(e,t,i){"use strict";var n=i(3238),r=i(5674),s=i(5354),o=i(1271);i(9291);var a=Array.prototype,c={DOMTokenList:!0,NodeList:!0};e.exports=function(e){var t=e.forEach;return e===a||s(a,e)&&t===a.forEach||r(c,n(e))?o:t}},7017:function(e,t,i){"use strict";var n=i(1246);e.exports=n},2590:function(e,t,i){"use strict";var n=i(7265);e.exports=n},9640:function(e,t,i){"use strict";var n=i(8705);e.exports=n},2480:function(e,t,i){"use strict";var n=i(1263);e.exports=n},8864:function(e,t,i){"use strict";var n=i(947);e.exports=n},7010:function(e,t,i){"use strict";var n=i(9271);e.exports=n},5825:function(e,t,i){"use strict";var n=i(5854);e.exports=n},7186:function(e,t,i){"use strict";var n=i(4029);e.exports=n},6832:function(e,t,i){"use strict";var n=i(7903);e.exports=n},9208:function(e,t,i){"use strict";var n=i(4399);e.exports=n},7975:function(e,t,i){"use strict";var n=i(2400);e.exports=n},6002:function(e,t,i){"use strict";var n=i(5357);i(9594),e.exports=n},8512:function(e,t,i){"use strict";i(3332);var n=i(8088);e.exports=n.setInterval},4978:function(e,t,i){"use strict";i(3332);var n=i(8088);e.exports=n.setTimeout},2131:function(e,t,i){"use strict";var n=i(148);i(9594),e.exports=n},1478:function(e,t,i){"use strict";var n=i(9278);e.exports=n},1234:function(e,t,i){"use strict";i(9573),i(7596),i(1555),i(8150);var n=i(8088);e.exports=n.URLSearchParams},9278:function(e,t,i){"use strict";i(1234),i(8069),i(199),i(949);var n=i(8088);e.exports=n.URL}},t={};function i(n){var r=t[n];if(void 0!==r)return r.exports;var s=t[n]={exports:{}};return e[n].call(s.exports,s,s.exports,i),s.exports}i.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return i.d(t,{a:t}),t},i.d=function(e,t){for(var n in t)i.o(t,n)&&!i.o(e,n)&&Object.defineProperty(e,n,{enumerable:!0,get:t[n]})},i.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(e){if("object"==typeof window)return window}}(),i.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},function(){"use strict";var e=i(8075),t=i.n(e),n=i(2608),r=i.n(n),s=i(1879),o=i.n(s),a=i(7286),c=i.n(a),l=i(6013),d=i.n(l),u=i(5103),h=i.n(u),g=i(7513),f=i.n(g),p=i(9524),v=i.n(p),b=i(145),m=i.n(b),y=class{constructor(){let e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:"adcsh",t=arguments.length>1&&void 0!==arguments[1]&&arguments[1];this.tagName=e,this.isDebugEnabled=t,t=localStorage.getItem("adcsh_dbg"),t&&(this.isDebugEnabled=JSON.parse(t))}#e(e,t){this.isDebugEnabled&&console.log(`[${this.tagName}][${e}]:`,...t)}debug(){for(var e=arguments.length,t=new Array(e),i=0;i<e;i++)t[i]=arguments[i];this.#e("debug",t)}error(){for(var e=arguments.length,t=new Array(e),i=0;i<e;i++)t[i]=arguments[i];this.#e("error",t)}},w=i(4369),x=i.n(w),k=i(576),A=i.n(k),S=i(4071),C=i.n(S),T=i(8001),O=i.n(T);const I=(e,t,i)=>e.addEventListener?e.addEventListener(t,i):e.attachEvent(`on${t}`,i),E=(e,t,i)=>{if(e.removeEventListener)return e.removeEventListener(t,i);e.detachEvent(`on${t}`,i)},R=async function(e){let t=arguments.length>1&&void 0!==arguments[1]&&arguments[1];return"undefined"!=typeof navigator&&"userAgentData"in navigator?navigator.userAgentData.getHighEntropyValues(["model","platform","platformVersion","uaFullVersion"]).then((e=>{const i={};if(e.hasOwnProperty("brands")&&e.brands.length>0){const t=[];for(let i=0;i<e.brands.length;i+=1){const n=e.brands[i];t.push(`"${n.brand}";v=${n.version}`)}i.chu=encodeURIComponent(t.join(", "))}e.hasOwnProperty("mobile")&&(i.chmob=encodeURIComponent(e.mobile?"?1":"?0"));const n={model:"chmod",platform:"chp",platformVersion:"chpv",uaFullVersion:"chuafv"};for(const t in n)e.hasOwnProperty(t)&&e[t]&&(i[n[t]]=encodeURIComponent(e[t]));if(t)return i;let r="";for(let e in i)r+=`&${e}=${i[e]}`;return r})).catch((t=>(e.error("error getting client hints:",t),""))):t?{}:""},P=()=>{let e=window.location.href;return $()&&(e=document.referrer),L(e)},$=()=>{try{return window.self!==window.top?1:0}catch(e){return 1}},L=e=>{let t=Math.max(x()(e).call(e," ",256),x()(e).call(e,",",256));return(t>384||t<20)&&(t=256),e.substring(0,t)},z=()=>{if(void 0===window.rgxngibqxq||""===window.rgxngibqxq){let e=[],t="0123456789abcdefghijklmnopqrstuvwxyz";for(let i=0;i<32;i++)e[i]=t.substr(Math.floor(16*Math.random()),1);e[14]="4",e[19]=t.substr(3&e[19]|8,1),window.rgxngibqxq=e.join("")}return window.rgxngibqxq},F=()=>window.innerWidth||document.documentElement.clientWidth||document.body.clientWidth,U=()=>window.innerHeight||document.documentElement.clientHeight||document.body.clientHeight,B=()=>{var e=document.title;if($())try{e=window.top.document.title}catch(t){e=""}return L(e)},N=()=>{var e=document.referrer;if($())try{e=window.top.document.referrer}catch(t){e=""}return L(e)},j=function(e){let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:null;try{for(var i=window.top.document.getElementsByTagName("meta"),n=0;n<i.length;n++)if(i[n].hasAttribute("name")&&i[n].getAttribute("name").toLowerCase()===e){var r=i[n].getAttribute("content");return L(r)}}catch(e){t&&t.error(e)}return""},M=/opera/i.test(navigator.userAgent),H=(/msie/i.test(navigator.userAgent)||/Trident/i.test(navigator.userAgent))&&!M,D=/chrome|crios/i.test(navigator.userAgent),_=/firefox/i.test(navigator.userAgent),V=(/safari/i.test(navigator.userAgent)&&!/chrome/i.test(navigator.userAgent)&&/opios/i.test(navigator.userAgent),(navigator.userAgent.match(/.+(?:ox|me|ra|ie|Edge)[\/: ]([\d.]+)/)||[])[1]),W=A()(V),q=/android/i.test(navigator.userAgent),G=/ipad|ipod|iphone/i.test(navigator.userAgent),Z=/blackberry/i.test(navigator.userAgent)||/BB10/i.test(navigator.userAgent),Q=/iemobile/i.test(navigator.userAgent)||/(?=.*\bWindows\b)(?=.*\bARM\b)/i.test(navigator.userAgent)||/Windows Phone/i.test(navigator.userAgent),K=/opera mini/i.test(navigator.userAgent)||/opios/i.test(navigator.userAgent),J=/^((?!UCWEB).)*UCBrowser.*Mobile.+/i.test(navigator.userAgent),Y=/(?:Nexus 7|BNTV250|Kindle Fire|Silk|GT-P1000)/i.test(navigator.userAgent),X=/(KFOT|KFTT|KFJWI|KFJWA|KFSOWI|KFTHWI|KFTHWA|KFAPWI|KFAPWA|KFARWI|KFASWI|KFSAWI|KFSAWA|JSS15J|Silk|Kindle)/i.test(navigator.userAgent),ee=/fban\/fbios|fbav|fbios|fb_iab\/fb4a/i.test(navigator.userAgent),te=q||G||Z||Q||K||J||Y||X||ee,ie=(document.documentElement,/^((?!UCWEB).)*UCBrowser.*Mobile$/i.test(navigator.userAgent),/^Mozilla\/5\.0 .+ Gecko\/$/i.test(navigator.userAgent),/pinterest\/(ios|android)/i.test(navigator.userAgent)),ne=function(e){let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:1,i=arguments.length>2&&void 0!==arguments[2]?arguments[2]:15;return((e,t)=>{let i="";for(let n=0;n<t;n++)i+=e[Math.floor(Math.random()*e.length)];return i})(e,Math.floor(Math.random()*(i-t+1))+t)},re=e=>{if((e=new(c())(e)).search){var t;const i=ne("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",20,21),n=C()(t=e.searchParams).call(t),r=m()(n);(e=>{for(let t=e.length-1;t>0;t--){const i=Math.floor(Math.random()*(t+1));[e[t],e[i]]=[e[i],e[t]]}})(r);const s=O()(r).call(r,(e=>`${e[0]}=${encodeURIComponent(e[1])}`)).join("&"),o=encodeURIComponent(btoa(s));e.search=`${i}=${o}`}return e.toString()},se=(()=>{try{return!0===new Request("",{keepalive:!0}).keepalive}catch(e){return!1}})();Math.random();var oe=i(8462),ae=i.n(oe),ce=i(653),le=i.n(ce),de=i(7950),ue=i.n(de);const he=e=>"boolean"==typeof e,ge=e=>ae()(e),fe=e=>"[object String]"===Object.prototype.toString.call(e),pe=e=>{var t;return ue()(t=["top","bottom"]).call(t,e)};var ve=i(7412),be=i.n(ve),me=i(414),ye=i.n(me),we=class{isCapped=!1;hasNoInventory=!1;show(){throw new Error("not implemented")}};const xe="interstitial",ke="pop",Ae="tabswap",Se="utsid-send";var Ce=(e,t,i,n,r)=>{const s=document.createElement("div");s.id="modal",s.style.position="fixed",s.style.top="5vh",s.style.left="50%",s.style.transform="translate(-50%)",s.style.maxWidth="95%",s.style.display="flex",s.style.flexDirection="column",s.style.alignItems="center",s.style.overflow="hidden",s.style.padding="10px",s.style.borderRadius="6px",s.style.backgroundColor="rgba(0, 0, 0, 0.6)",s.style.zIndex="2147483646",s.style.boxShadow="0 4px 8px rgba(0,0,0,0.2)",s.setAttribute("doskip","1"),s.setAttribute("prclck","1");const o=document.createElement("div");o.id="buttonContainer",o.style.display="block",o.style.margin="0",o.style.width="100%",o.style.textAlign="center",o.style.padding="0",o.style.height="36px",o.style.fontSize="16px",o.style.fontFamily='OpenSans-Semibold, Arial, "Helvetica Neue", Helvetica, sans-serif';const a=document.createElement("a");a.id="goToButton",a.style.float="left",a.style.borderRadius="4px",a.style.fontSize="12px",a.style.background="rgb(0, 0, 0)",a.style.opacity="1",a.style.textDecoration="none",a.style.color="rgb(255, 255, 255)",a.style.padding="10px 20px",a.style.cursor="pointer",a.style.display="inline-block",a.textContent=e,a.href=t,a.target="_blank",a.rel="noopener noreferrer";const c=document.createElement("div");c.id="closeButton",c.style.float="right",c.style.borderRadius="4px",c.style.fontSize="12px",c.style.background="rgb(0, 0, 0)",c.style.opacity="1",c.style.textDecoration="none",c.style.color="rgb(255, 255, 255)",c.style.padding="10px 20px",c.style.cursor="pointer",c.style.display="inline-block",c.textContent=i;const l=document.createElement("div");l.id="content",l.style.marginTop="10px",l.style.maxWidth="100%";const d=document.createElement("img");return d.id="impImg",d.style.display="none",d.width="0",d.height="0",d.src=r,o.appendChild(a),o.appendChild(c),s.appendChild(o),l.appendChild(n),s.appendChild(l),s.appendChild(d),s},Te=e=>{const t=document.createElement("iframe");function i(){const e=window.innerWidth;e<=600?(t.style.width="90vw",t.style.height="70vh"):e>600&&e<=1024?(t.style.width="80vw",t.style.height="70vh"):(t.style.width="60vw",t.style.height="70vh")}return t.id="creative_iframe",t.setAttribute("allowfullscreen",""),t.setAttribute("frameborder","0"),t.setAttribute("doskip","1"),t.setAttribute("prclck","1"),t.setAttribute("sandbox","allow-same-origin allow-scripts allow-popups allow-forms"),t.setAttribute("referrerpolicy","no-referrer"),t.src=e,t.style.margin="0",t.style.padding="0",t.style.border="0",i(),window.addEventListener("resize",i),{content:t,resizeFunc:i}},Oe=(e,t,i,n)=>{const r=document.createElement("a");r.id="a_click_link",r.href=e,r.rel="noopener noreferrer",r.target="_blank",r.style.display="block";const s=document.createElement("img");function o(){window.innerWidth/window.innerHeight>=1?(s.style.height="75vh",s.style.width="auto"):(s.style.height="auto",s.style.width="90vw")}return s.id="creative_image",s.src=t,s.alt="",s.setAttribute("referrerpolicy","no-referrer"),s.style.maxWidth=i+"px",s.style.maxHeight=n+"px",s.style.width="90vw",r.appendChild(s),o(),window.addEventListener("resize",o),{content:r,resizeFunc:o}},Ie=e=>{const t=document.createElement("iframe");function i(){const e=window.innerWidth;e<=600?(t.style.maxWidth="90vw",t.style.height="70vh"):e>600&&e<=1024?(t.style.maxWidth="80vw",t.style.height="70vh"):(t.style.maxWidth="60vw",t.style.minHeight="40vh")}return t.id="creative_iframe",t.setAttribute("allowfullscreen",""),t.setAttribute("frameborder","0"),t.setAttribute("doskip","1"),t.setAttribute("sandbox","allow-same-origin allow-scripts allow-popups allow-forms"),t.setAttribute("referrerpolicy","no-referrer"),t.setAttribute("rel","noopener noreferrer"),t.setAttribute(e,"1"),t.style.margin="0",t.style.padding="0",t.style.border="0",i(),window.addEventListener("resize",i),{content:t,resizeFunc:i}},Ee=(e,t,i,n,r)=>{const s=document.createElement("div");s.id="modal",s.style.textAlign="left",s.style.width="100%",s.style.height="100%",s.style.position="fixed",s.style.inset="0",s.style.zIndex="2147483646",s.style.backgroundColor="rgba(0,0,0,0.8)",s.setAttribute("doskip","1"),s.setAttribute("prclck","1");const o=document.createElement("div");o.id="buttonContainer",o.style.display="block",o.style.textAlign="center",o.style.padding="0",o.style.height="36px",o.style.fontSize="16px",o.style.fontFamily='OpenSans-Semibold, Arial, "Helvetica Neue", Helvetica, sans-serif',o.style.margin="6px 15px";const a=document.createElement("a");a.id="goToButton",a.style.float="left",a.style.borderRadius="4px",a.style.fontSize="16px",a.style.background="rgb(0, 0, 0)",a.style.textDecoration="none",a.style.color="rgb(255, 255, 255)",a.style.padding="10px 20px",a.style.cursor="pointer",a.style.display="inline-block",a.textContent=e,a.href=t,a.target="_blank",a.rel="noopener noreferrer";const c=document.createElement("div");c.id="closeButton",c.style.float="right",c.style.borderRadius="4px",c.style.fontSize="16px",c.style.background="rgb(0, 0, 0)",c.style.textDecoration="none",c.style.color="rgb(255, 255, 255)",c.style.padding="10px 20px",c.style.cursor="pointer",c.style.display="inline-block",c.textContent=i;const l=document.createElement("div");l.id="content",l.style.marginTop="10px",l.style.display="flex",l.style.justifyContent="center",l.style.width="100%",l.style.height="100%";const d=document.createElement("img");return d.id="impImg",d.style.display="none",d.width="0",d.height="0",d.src=r,o.appendChild(a),o.appendChild(c),s.appendChild(o),l.appendChild(n),s.appendChild(l),s.appendChild(d),s},Re=e=>{const t=document.createElement("iframe");return t.id="creative_iframe",t.setAttribute("allowfullscreen",""),t.setAttribute("frameborder","0"),t.setAttribute("doskip","1"),t.setAttribute("prclck","1"),t.setAttribute("sandbox","allow-same-origin allow-scripts allow-popups allow-forms"),t.setAttribute("referrerpolicy","no-referrer"),t.src=e,t.style.margin="0",t.style.padding="0",t.style.border="0",t.style.width="100%",t.style.height="100%",{content:t,resizeFunc:null}},Pe=(e,t,i,n)=>{const r=document.createElement("a");r.id="a_click_link",r.href=e,r.rel="noopener noreferrer",r.target="_blank",r.style.display="block";const s=document.createElement("img");function o(){window.innerWidth>window.innerHeight?(s.style.width="auto",s.style.height="75vh"):(s.style.width="95vw",s.style.height="auto")}return s.id="creative_image",s.src=t,s.alt="",s.setAttribute("referrerpolicy","no-referrer"),s.style.maxWidth=i+"px",s.style.maxHeight=n+"px",s.style.width="95vw",r.appendChild(s),o(),window.addEventListener("resize",o),{content:r,resizeFunc:o}},$e=e=>{const t=document.createElement("iframe");return t.id="creative_iframe",t.setAttribute("allowfullscreen",""),t.setAttribute("frameborder","0"),t.setAttribute("doskip","1"),t.setAttribute("sandbox","allow-same-origin allow-scripts allow-popups allow-forms"),t.setAttribute("referrerpolicy","no-referrer"),t.setAttribute("rel","noopener noreferrer"),t.setAttribute(e,"1"),t.style.margin="0",t.style.padding="0",t.style.border="0",t.style.width="100%",t.style.height="100%",{content:t,resizeFunc:null}};const Le="utsid-send",ze=2147483647,Fe="dontfoid",Ue="donto",Be="znid",Ne="prclck";var je=class{#t={};#i=null;#n=0;#r;#s;#o;constructor(e,t,i,n,r){this.#t=e,this.#i=i,this.#n=0,this.#r=t,this.#s=n,this.#o=r}render(e){let t=null;switch(e.type){case 1:this.#i.debug(`rendering INTERSTITIAL IFRAME (type 1) in ${this.#t.isOverlay?"OVERLAY":"FULLSCREEN"} mode`),t=this.#t.isOverlay?Te(e.url):Re(e.url);break;case 3:this.#i.debug(`rendering INTERSTITIAL IMAGE (type 3) in ${this.#t.isOverlay?"OVERLAY":"FULLSCREEN"} mode`),t=this.#t.isOverlay?Oe(e.url,e.ad.url,e.ad.width,e.ad.height):Pe(e.url,e.ad.url,e.ad.width,e.ad.height);break;case 4:if(e.isHtmlTemplate)return this.#i.debug("rendering INTERSTITIAL HTML CUSTOM (type 4)"),void this.#a(e);this.#i.debug(`rendering INTERSTITIAL HTML (type 4) in ${this.#t.isOverlay?"OVERLAY":"FULLSCREEN"} mode`),t=this.#t.isOverlay?Ie(Ne):$e(Ne);break;default:return void this.#i.error(`no such type of interstitial: ${e.type}`)}const i=document.createElement("div");document.body.appendChild(i);const n=i.attachShadow({mode:"open"}),r=this.#t.isOverlay?Ce:Ee;if(n.appendChild(r(this.#t.texts.goToButton,e.url,this.#c(),t.content,e.iurl)),4===e.type){const t=n.getElementById("creative_iframe");t.contentWindow.contents=e.html,t.src='javascript:window["contents"]'}if(!this.#t.disableCountdown&&this.#t.moveTimerInsideButtonAfter>0){this.#n=this.#t.moveTimerInsideButtonAfter,n.getElementById("closeButton").innerHTML=this.#c();const e=d()((()=>{this.#n--,n.getElementById("closeButton").innerHTML=this.#c(),0===this.#n&&clearInterval(e)}),1e3)}n.getElementById("closeButton").addEventListener("click",(()=>{this.#n>0||(this.#i.debug("close button click. remove modal host, resize listener if present and do callback"),i.remove(),t.resizeFunc&&window.removeEventListener("resize",t.resizeFunc),this.#r(xe))}))}#c(){let e=`${this.#t.texts.pleaseWait}: ${this.#n} ${this.#t.texts.timePlural}`;return 1===this.#n&&(e=`${this.#t.texts.pleaseWait}: ${this.#n} ${this.#t.texts.timeSingle}`),0===this.#n&&(e=this.#t.disableCountdown?this.#t.texts.xLabel:this.#t.texts.skipAd),e}#a(e){const t=(new DOMParser).parseFromString(e.html,"text/html").querySelector("script"),i=document.createElement("script");i.style.zIndex="2147483646",t.src?i.setAttribute("src",t.src):i.innerText=t.innerText;const n=()=>{this.#i.debug("CT-CLICK"),fetch(e.link,{mode:"no-cors"}),E(document,"ct-click",n)},r=()=>{this.#i.debug("CT-CLOSE"),E(document,"ct-click",n),E(document,"ct-close",r),document.body.removeChild(i),this.#r(xe)};I(document,"ct-click",n),I(document,"ct-close",r);let s=e.iurl;window[Le]&&(s+=`&utsid=${window[Le]}`),s+=`&cbpage=${encodeURIComponent(P())}`,s+=`&cbref=${encodeURIComponent(N())}`,i.onload=async()=>{try{await fetch(s.toString())}catch(e){return this.#i.debug(e),void(this.#o&&!this.#s.isAdbMode()&&(this.#i.debug("imp failed: try alt domain and path"),this.#s.enableAdbMode()))}document.dispatchEvent(new CustomEvent("impression-event"))},i.onerror=()=>{this.#i.debug("custom html script failed to load"),this.#r(xe)},document.body.appendChild(i)}},Me=class extends we{#l;#d;#u;#h;#g;#f;#p;#r;#v;#b;#s;#i;#m=!1;#t={};isCapped=!1;hasNoInventory=!1;#y=null;#o;#w=12;#x="52.5";#k=null;#A=!1;#S=!1;#C;constructor(e){super(),this.#i=new y(`atag_${e.collectiveZoneId}_interstitial_${e.zoneId}`),this.#i.debug("init atag interstitial with config:",e),this.#l=e.zoneId,this.#d=e.isFullscreen,this.#o=e.adblockSettings,this.#u=e.collectiveZoneId,this.#h=e.aggressivity,this.#g=e.recordPageView,this.#f=e.adsCapping,this.#p=e.abTest,this.#g=e.recordPageView,this.#r=e.actionCallback,this.#v=e.adserverDomain,this.#s=window[e.adcashGlobalName],this.#b=e.clientHintsQueryStr,this.#S=e.isLoadedAsPartOfLibrary,this.#C=e.uniqueFingerprint,e.tagVersionSuffix&&(this.#x+=e.tagVersionSuffix)}show(e){const t=this.#T(e);fetch(t).then((e=>200===e.status||202===e.status?e.json():(204===e.status&&(this.hasNoInventory=!0,this.#i.debug(`no inventory! reset after ${this.#w} sec`),f()((()=>{this.hasNoInventory=!1}),1e3*this.#w),this.#w<7200&&(this.#w*=5)),ye().reject()))).then((e=>{if(this.#i.debug("response:",e),e.capped_ttl)return this.isCapped=!0,this.#i.debug(`capped! reset after ${e.capped_ttl} sec`),f()((()=>{this.isCapped=!1}),1e3*e.capped_ttl),void this.#r(xe);this.#w>12&&(this.#w=12),this.#m?this.#y=e:(this.#i.debug("initial request. configure"),this.#m=!0,this.#t={moveTimerInsideButtonAfter:e.moveTimerInsideButtonAfter,delay:e.delay,refreshRate:e.refreshRate,isOverlay:e.isOverlay,disableCountdown:e.disableCountdown,texts:e.texts,showOnInnerLinkClick:e.showOnInnerLinkClick},this.#y=e.adPayload,this.#k=new je(this.#t,this.#r,this.#i,this.#s,this.#o)),this.#b&&(this.#y.url+=this.#b,this.#y.iurl+=this.#b,this.#y.clickPixelUrl&&(this.#y.clickPixelUrl+=this.#b)),4===this.#y.type&&this.#y.html&&(this.#y.html=`<!DOCTYPE html><html><head><meta name="referrer" content="no-referrer"></head><body>${this.#y.html}</body></html>`),this.#O()})).catch((e=>{if(e&&this.#i.error(e),e&&this.#o&&!this.#A)return this.#i.debug("fetch call failed. Switch to adblck domain and path"),this.#A=!0,this.#s.enableAdbMode(),void this.show();this.#r(xe)}))}#O(){this.#i.debug("render"),this.#k.render(this.#y)}#T(e){let t=`${window.location.protocol}//${this.#v}/script/interstitial.php`;if(this.#o&&this.#s.isAdbMode()){const{adserverDomain:e}=this.#o,i=`/${ne("abcdefgh0123456789")}`;t=`${window.location.protocol}//${e}${i}`}return t+=`?r=${this.#l}`,this.#m&&(t+="&rbd=1"),this.#b&&(t+=this.#b),t=t+"&atag=1"+`&czid=${this.#u}`+`&aggr=${this.#h}`+`&seqid=${e}`+`&ufp=${encodeURIComponent(this.#C)}`+`&srs=${this.#s.getSesionRandomString()}`+`&cbpage=${encodeURIComponent(P())}`+`&atv=${this.#x}`+`&cbref=${encodeURIComponent(N())}`,this.#o&&(t+="&abtg=1"),this.#g&&(t+="&ppv=1"),this.#p&&(t+=`&ab_test=${this.#p}`),!1===this.#f&&(t+="&cap=0"),this.#o&&this.#o.adbVersion&&(t+=`&adbv=${this.#o.adbVersion}`),this.#o&&this.#s.isAdbMode()?(t+="&sadbl=2",t+="&fmt=intrn",this.#i.debug(`bid url: ${t}`),re(t)):(this.#i.debug(`bid url: ${t}`),t)}};const He="znid";var De=class{targetElementsCssSelector=null;shouldTriggerPopOnTargetClick=!1;constructor(e,t,i){this.targetElementsCssSelector=e,this.shouldTriggerPopOnTargetClick=t,this.zoneId=i}isPresent(){return!!this.targetElementsCssSelector}isActionAllowedOnElement(e){if(!this.isPresent())return!0;if(e.hasAttribute(He))return e.getAttribute(He)===this.zoneId;if(e.hasAttribute("doskip"))return!1;const t=m()(document.querySelectorAll('[doskip*="1"]'));for(const i of t)if(i.contains(e))return!1;return this.#I(e)?this.shouldTriggerPopOnTargetClick:!this.shouldTriggerPopOnTargetClick}#I(e){const t=document.querySelectorAll(this.targetElementsCssSelector);do{for(let i=0;i<t.length;i++)if(e===t[i])return!0}while(e=e.parentNode);return!1}},_e=class{observer=null;iframesToOverlays=[];videosToOverlays=[];anchorsToOverlays=[];fullOverlay=null;overlaysResizeIntervalChecker=null;adUrl="";isTabSwap=!1;modifyBodyObserver=!0;#i;#l;#E=!1;constructor(e,t,i,n,r){this.elementTargeting=e,this.desktopClickListener=t,this.#i=i,this.#l=n,this.#E=r}setOverlaysResizeIntervalChecker(){this.overlaysResizeIntervalChecker=d()((()=>{var e,t,i;const n=(e,t)=>{try{const i=t.getBoundingClientRect();e.style.top=`${i.top+window.scrollY}px`,e.style.left=`${i.left+window.scrollX}px`,e.style.width=`${i.width}px`,e.style.height=`${i.height}px`}catch(e){}};r()(e=this.iframesToOverlays).call(e,(e=>{let{overlay:t,iframe:i}=e;return n(t,i)})),r()(t=this.videosToOverlays).call(t,(e=>{let{overlay:t,video:i}=e;return n(t,i)})),r()(i=this.anchorsToOverlays).call(i,(e=>{let{overlay:t,anchor:i}=e;return n(t,i)}))}),500)}clearOverlaysResizeIntervalChecker(){try{clearInterval(this.overlaysResizeIntervalChecker)}catch(e){}}#R(e){const t=document.createElement("div");if(t.addEventListener("mousedown",(e=>{this.#i.debug("mousedown on overlay"),e.stopPropagation(),e.preventDefault(),this.desktopClickListener(e)}),this.#E),e===document.body)t.id="dontfoid",t.style.top="0px",t.style.left="0px",t.style.width=`${window.innerWidth||document.documentElement.clientWidth||document.body.clientWidth}px`,t.style.height=`${window.innerHeight||document.documentElement.clientHeight||document.body.clientHeight}px`,t.style.position="fixed";else{const i=e.getBoundingClientRect();t.style.top=`${i.top+window.scrollY}px`,t.style.left=`${i.left+window.scrollX}px`,t.style.width=`${i.width}px`,t.style.height=`${i.height}px`,t.style.position="absolute",t.setAttribute("donto","")}return t.setAttribute(He,this.#l),t.style.zIndex=2147483647,t.style.backgroundColor="transparent",e===document.body?document.body.appendChild(t):e.parentNode.appendChild(t),t}attachVideoOverlays(){const e=document.querySelectorAll("video");for(let t=0;t<e.length;t++)this.elementTargeting.isActionAllowedOnElement(e[t])&&this.videosToOverlays.push({video:e[t],overlay:this.#R(e[t])})}attachIframeOverlays(){const e=document.querySelectorAll("iframe");for(let t=0;t<e.length;t++)this.elementTargeting.isActionAllowedOnElement(e[t])&&this.iframesToOverlays.push({iframe:e[t],overlay:this.#R(e[t])})}attachAnchorOverlays(){const e=document.querySelectorAll("a");for(let t=0;t<e.length;t++)this.elementTargeting.isActionAllowedOnElement(e[t])&&this.anchorsToOverlays.push({anchor:e[t],overlay:this.#R(e[t])})}clearVideoOverlays(){for(let e=0;e<this.videosToOverlays.length;e++)this.videosToOverlays[e].overlay.parentNode.removeChild(this.videosToOverlays[e].overlay),this.videosToOverlays[e].overlay=null;this.videosToOverlays.length=0}clearAnchorOverlays(){for(let e=0;e<this.anchorsToOverlays.length;e++)this.anchorsToOverlays[e].overlay.parentNode.removeChild(this.anchorsToOverlays[e].overlay),this.anchorsToOverlays[e].overlay=null;this.anchorsToOverlays.length=0}clearIframeOverlays(){for(let e=0;e<this.iframesToOverlays.length;e++)this.iframesToOverlays[e].overlay.parentNode.removeChild(this.iframesToOverlays[e].overlay),this.iframesToOverlays[e].overlay=null;this.iframesToOverlays.length=0}};const Ve=6e5;var We=class extends we{#s;#y=null;#t={};#P=!1;#$;#m=!1;#E=!0;#i;#x="52.5";#A=!1;#L=null;#w=12;constructor(e){var t;super(),this.#i=new y(`atag_${e.collectiveZoneId}_suv5_${e.zoneId}`),this.#s=window[e.adcashGlobalName],this.#i.debug("init atag pop with config:",e),this.#t=e,this.elementTargeting=new De(this.#t.targetElementsCssSelector,this.#t.triggerOnTargetElementsClick,this.#t.zoneId),te&&(this.#i.debug("use capture -> false"),this.#E=!1),this.overlays=new _e(this.elementTargeting,v()(t=this.#z).call(t,this),this.#i,this.#t.zoneId,this.#E),e.tagVersionSuffix&&(this.#x+=e.tagVersionSuffix),this.#i.debug("tag version:",this.#x)}show(){this.#y=null,this.#$=null,this.#P=!1,fetch(this.#T()).then((e=>200===e.status||202===e.status?e.json():(204===e.status&&(this.hasNoInventory=!0,this.#i.debug(`no inventory! reset after ${this.#w} sec`),f()((()=>{this.hasNoInventory=!1}),1e3*this.#w),this.#w<7200&&(this.#w*=5)),ye().reject()))).then((e=>{if(this.#i.debug("response:",e),e.capped_ttl)return this.isCapped=!0,this.#i.debug(`capped! reset after ${e.capped_ttl} sec`),f()((()=>{this.isCapped=!1}),1e3*e.capped_ttl),void this.#t.actionCallback(ke);if(this.#w>12&&(this.#w=12),!this.#m){this.#m=!0;const t=e.delay??0;return this.#i.debug("delay is",t),void f()((()=>{this.#F(e)}),1e3*t)}this.#F(e)})).catch((e=>{if(e&&this.#i.error(e),e&&this.#t.adblockSettings&&!this.#A)return this.#i.debug("fetch call failed. Switch to adblck domain and path"),this.#s.enableAdbMode(),this.#A=!0,void this.show();this.#t.actionCallback(ke)}))}#T(){let e=`${window.location.protocol}//${this.#t.adserverDomain}/script/suurl5.php`;if(this.#t.adblockSettings&&this.#s.isAdbMode()){const{adserverDomain:t}=this.#t.adblockSettings,i=`/${ne("abcdefgh0123456789")}`;e=`${window.location.protocol}//${t}${i}`}if(e+=`?r=${this.#t.zoneId}`,this.#m&&(e+="&rbd=1"),this.#t.targetCountries){const t=this.#t.targetCountries.join(",");this.#t.triggerOnTargetCountries?e+="&allowed_countries="+encodeURIComponent(t):e+="&excluded_countries="+encodeURIComponent(t)}return e=e+this.#t.clientHintsQueryStr+"&atag=1&cbur="+Math.random()+"&cbiframe="+$()+"&cbWidth="+F()+"&cbHeight="+U()+"&cbtitle="+encodeURIComponent(B())+"&cbpage="+encodeURIComponent(P())+"&cbref="+encodeURIComponent(N())+"&cbdescription="+encodeURIComponent(j("description"))+"&cbkeywords="+encodeURIComponent(j("keywords"))+"&cbcdn="+encodeURIComponent(this.#s.getCdnDomain())+"&ts="+be()()+"&atv="+this.#x+"&ufp="+encodeURIComponent(this.#t.uniqueFingerprint)+"&srs="+this.#s.getSesionRandomString(),this.#t.adblockSettings&&(e+="&abtg=1"),this.#t.aggressivity&&(e+=`&aggr=${this.#t.aggressivity}`),this.#t.collectiveZoneId&&(e+=`&czid=${this.#t.collectiveZoneId}`),this.#t.recordPageView&&(e+="&ppv=1"),this.#t.abTest&&(e+=`&ab_test=${this.#t.abTest}`),!1===this.#t.adsCapping&&(e+="&cap=0"),this.#t.adblockSettings&&this.#t.adblockSettings.adbVersion&&(e+=`&adbv=${this.#t.adblockSettings.adbVersion}`),this.#t.adblockSettings&&this.#s.isAdbMode()?(e+="&sadbl=2",e+="&fmt=suv5",this.#i.debug(`bid url: ${e}`),re(e)):(this.#i.debug(`bid url: ${e}`),e)}#U(e){try{let t=this.#L?this.#L(""):window.open("");return t.document.open(),t.document.writeln('<meta name="referrer" content="no-referrer"><script type="text/javascript">window.location = "'+e+'";<\/script>'),t.document.close(),t}catch(e){return this.#i.error("window open failed:",e),null}}#B(){var e;if("complete"===document.readyState&&void 0!==document.body){var t;const e=document.createElement("iframe");return e.width="0",e.height="0",e.tabindex="-1",e.style="position:absolute;top:-1000px;left:-1000px;visibility:hidden;border:medium none;background-color:transparent;",document.body.appendChild(e),void(this.#L=v()(t=e.contentWindow.open).call(t,e.contentWindow))}f()(v()(e=this.#B).call(e,this),50)}#F(e){this.#y={url:this.#N(e.url),impressionUrl:e.iurl,refreshRate:e.refreshRate,delay:e.delay,type:e.type},e.targetElementsCssSelector&&!this.elementTargeting.targetElementsCssSelector&&(this.elementTargeting.targetElementsCssSelector=e.targetElementsCssSelector,this.elementTargeting.shouldTriggerPopOnTargetClick=e.triggerOnTargetElementsClick),this.overlays.attachAnchorOverlays(),this.overlays.attachIframeOverlays(),this.overlays.attachVideoOverlays(),this.overlays.setOverlaysResizeIntervalChecker(),this.#j(),this.#i.debug("ready to show ad")}#M(){return"type"in this.#y&&"tabswap"===this.#y.type}#H(){this.#i.debug("do tabswap"),this.#t.actionCallback(Ae);const e=this.#y.url;this.#L?this.#$=this.#L(window.location.href,"_blank","noreferrer"):this.#$=window.open(window.location.href,"_blank","noreferrer"),this.#D().finally((()=>{f()((()=>{const t=document.createElement("a");t.href=e,t.rel="noopener noreferrer",document.body.appendChild(t),t.click(),document.body.removeChild(t)}),50)}))}async#D(){let e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:0;const t=this.#$?"1":"0";this.#i.debug("window opened:",t);let i=this.#y.impressionUrl+`&wo=${t}`;if(window["utsid-send"]&&(i+=`&utsid=${window["utsid-send"]}`),e>0&&(this.#i.debug(`retry impression. Attempt ${e}`),i+=`&rtry=${e}`),i=i+this.#t.clientHintsQueryStr+"&cbpage="+encodeURIComponent(P())+"&cbref="+encodeURIComponent(N()),this.#i.debug("send impression. url:",i),se){this.#i.debug("keepalive supported!");let t=null,n=!1;try{t=await fetch(i,{keepalive:!0})}catch(e){if(this.#i.error(e),this.#t.adblockSettings&&!this.#s.isAdbMode())return this.#i.debug("imp failed: try alt domain and path"),void this.#s.enableAdbMode();n=!0}if(t&&!t.ok||n)return void(e<4&&(await this.#D(e+1),document.dispatchEvent(new CustomEvent("impression-retry-event"))))}else navigator.sendBeacon?(this.#i.debug("keepalive NOT supported! use sendBeacon"),navigator.sendBeacon(i)):(this.#i.debug("keepalive NOT supported! use image.src"),(new Image).src=i);document.dispatchEvent(new CustomEvent("impression-event"))}#_(){this.overlays.clearOverlaysResizeIntervalChecker(),this.overlays.clearAnchorOverlays(),this.overlays.clearIframeOverlays(),this.overlays.clearVideoOverlays(),this.#y=null,this.#V(),this.#s.isShowingPop=!1,this.#t.actionCallback(ke)}#z(e){this.#i.debug(`showAdClickListener triggered by event type ${e.type} on ${e.target.tagName}`),e.isTrusted?this.#y?this.#P?this.#i.debug(`${e.type} on ${e.target.tagName}:pop rejected: current pop is locked`):this.#s.isShowingPop?this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: another pop is being currently shown`):this.elementTargeting.isActionAllowedOnElement(e.target)?(this.#s.isShowingPop=!0,this.#P=!0,this.#i.debug("triggering pop"),this.#M()?this.#H():(this.#L?this.#$=this.#L(this.#y.url,"_blank","noopener,noreferrer"):this.#$=window.open(this.#y.url,"_blank","noopener,noreferrer"),this.#D().finally((()=>{this.#_()})))):this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: action not allowed on element`,e.target):this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: current pop has no ad loaded`):this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: event is not trusted`)}#N(e){let t=e;return D&&W<59||_&&W<56?t='data:text/html;charset=utf-8, <html><meta http-equiv="refresh" content="0;URL='+e+'"></html>':G&&D&&!M&&W>63&&(e="googlechrome://"+e.replace(/(^\w+:|^)\/\//,"")),t}#j(){var e;const t={zoneId:this.#t.zoneId,callback:v()(e=this.#z).call(e,this)};te&&ie&&(this.#i.debug("subscribe to scroll"),this.#s.subscribe("scroll",t)),te||(this.#i.debug("subscribe to mousedown"),this.#s.subscribe("mousedown",t,this.#E)),this.#i.debug("subscribe to click"),this.#s.subscribe("click",t,this.#E)}#V(){te&&ie&&(this.#i.debug("unsubscribe from scroll"),this.#s.unsubscribe("scroll",this.#t.zoneId)),te||(this.#i.debug("unsubscribe from mousedown"),this.#s.unsubscribe("mousedown",this.#t.zoneId,this.#E)),this.#i.debug("unsubscribe from click"),this.#s.unsubscribe("click",this.#t.zoneId,this.#E)}},qe=class{constructor(e){this.key=e}isStatePresent(){return null!==window.localStorage.getItem(this.key)}getState(){return JSON.parse(window.localStorage.getItem(this.key))}setState(e){window.localStorage.setItem(this.key,o()(e))}removeState(){window.localStorage.removeItem(this.key)}},Ge=class{#i;#s;#W=null;#q=null;#u;#G=[];#Z=0;#Q=null;#K=1;#J=0;#Y=!1;constructor(e){var t,i;const{adcashGlobalName:n,collectiveZoneConfig:r,adserverDomain:s,adblockSettings:o,clientHintsQueryStr:a,tagVersionSuffix:c,isLoadedAsPartOfLibrary:l,uniqueFingerprint:d}=e,{collectiveZoneId:u}=r;this.#i=new y(`atag_${u}`),this.#s=window[e.adcashGlobalName],this.#G=r.rotationList,this.#i.debug("init autotag with config:",e);const h=r.indexedFormats;let g=!0;for(const e in h){const f=h[e];switch(e){case"ippg":this.#s.runInPagePush({zoneId:f.zoneId.toString(),refreshRate:f.rr,delay:f.d,maxAds:f.mads,renderPosDesktop:f["render-pos-desktop"],renderPosMobile:f["render-pos-mobile"],offsetTop:f["offset-top"],isAutoTag:!0,collectiveZoneId:u,aggressivity:r.aggressivity,abTest:r.ab_test,recordPageView:g,tagVersionSuffix:c});break;case"suv4":case"pop":this.#q=new We({zoneId:f.zoneId.toString(),targetElementsCssSelector:f["element-list"],triggerOnTargetElementsClick:"allow"===f["element-action"],targetCountries:f["country-list"],triggerOnTargetCountries:"allow"===f["country-action"],adblockSettings:o,adserverDomain:s,adcashGlobalName:n,clientHintsQueryStr:a,collectiveZoneId:u,aggressivity:r.aggressivity,adsCapping:r.adsCapping,abTest:r.ab_test,recordPageView:g,actionCallback:v()(t=this.actionCallback).call(t,this),tagVersionSuffix:c,isLoadedAsPartOfLibrary:l,uniqueFingerprint:d});break;case"interstitial":this.#W=new Me({zoneId:f.zoneId,isFullscreen:0===f.overlay,adblockSettings:o,adserverDomain:s,adcashGlobalName:n,clientHintsQueryStr:a,collectiveZoneId:u,aggressivity:r.aggressivity,adsCapping:r.adsCapping,abTest:r.ab_test,recordPageView:g,actionCallback:v()(i=this.actionCallback).call(i,this),tagVersionSuffix:c,isLoadedAsPartOfLibrary:l,uniqueFingerprint:d});break;default:this.#i.error(`ad format type not recognised from collective zone config. adformat.type: ${e}; czid: ${czid}`)}}this.localStorageService=new qe(`atg_${u}`);const f=this.localStorageService.getState();f&&f.adbExpiresAt>be()()&&this.#s.enableAdbMode(),f&&f.expiresAt>be()()?(this.#i.debug("previous session present:",f),this.#K=f.shownAdsCounter,this.#J=f.iterationCounter,this.#Z=f.currentAdIndex,f.isInterstitialBeingShown?this.#X():(this.#Q=this.#G[this.#Z],this.#ee())):(this.#Q=this.#G[this.#Z],this.#ee())}actionCallback(e){this.#i.debug("ACTION CALLBACK type:",e),e===xe?this.#Y=!1:this.#K++;const t=this.#Q.rotationInterval;var i;this.#te(),this.#ie(),e===Ae?this.#i.debug("tabswap, move to next and store session"):(this.#i.debug(`show next ad after ${t} sec`),f()(v()(i=this.#ee).call(i,this),1e3*t))}#ie(){const e={shownAdsCounter:this.#K,iterationCounter:this.#J,currentAdIndex:this.#Z,isInterstitialBeingShown:this.#Y,expiresAt:be()()+6e5,adbExpiresAt:this.#s.isAdbMode()?be()()+Ve:0};this.#i.debug("store session state",e),this.localStorageService.setState(e)}#ne(){if(!this.#Q.apply)return!1;switch(this.#Q.apply){case"1st":return!(0===this.#J);case"odd":return!(this.#J%2==1);case"even":return!(this.#J%2==0);default:return!1}}#te(){this.#Z===this.#G.length-1?(this.#Z=0,this.#J++):this.#Z++,this.#Q=this.#G[this.#Z],this.#i.debug("set current ad to next on list. current ad is set to:",this.#Q)}#X(){this.#i.debug("show next ad"),this.#te(),this.#ie(),this.#ee()}#ee(){if(this.#ne())return this.#i.debug(`skipping ad at index: ${this.#Z} due to apply rule`),void this.#X();switch(this.#Q.type){case"interstitial":var e;if(this.#W.isCapped||this.#W.hasNoInventory)return void f()(v()(e=this.#X).call(e,this),1e3);this.#i.debug("showing interstitial"),this.#W.show(this.#K),this.#Y=!0,this.#K++,this.#ie();break;case"pop":var t;if(this.#q.isCapped||this.#q.hasNoInventory)return void f()(v()(t=this.#X).call(t,this),1e3);this.#i.debug("showing pop"),this.#q.show(this.#K);break;default:throw Error(`rotation list element type '${this.#Q.type}' not recognised`)}}},Ze=i(8333),Qe=i.n(Ze);const Ke=function(){this.element===window?(this.divOverlay.style.width=`${window.innerWidth||document.documentElement.clientWidth||document.body.clientWidth}px`,this.divOverlay.style.height=`${window.innerHeight||document.documentElement.clientHeight||document.body.clientHeight}px`):(this.divOverlay.style.top=`${this.element.offsetTop}px`,this.divOverlay.style.left=`${this.element.offsetLeft}px`,this.divOverlay.style.width=`${this.element.offsetWidth}px`,this.divOverlay.style.height=`${this.element.offsetHeight}px`,this.divOverlay.style.zIndex=ze)};var Je=class{observer=null;iframesToOverlays=[];videosToOverlays=[];anchorsToOverlays=[];fullOverlay=null;overlaysResizeIntervalChecker=null;adUrl="";isTabSwap=!1;modifyBodyObserver=!0;#i;#l;#E=!1;constructor(e,t,i,n,r,s){this.elementTargeting=e,this.desktopClickListener=t,this.mobileClickListener=i,this.#i=n,this.#l=r,this.#E=s}setOverlaysResizeIntervalChecker(){this.overlaysResizeIntervalChecker=d()((()=>{var e,t,i;const n=(e,t)=>{try{const i=t.getBoundingClientRect();e.style.top=`${i.top+window.scrollY}px`,e.style.left=`${i.left+window.scrollX}px`,e.style.width=`${i.width}px`,e.style.height=`${i.height}px`}catch(e){}};r()(e=this.anchorsToOverlays).call(e,(e=>{let{overlay:t,anchor:i}=e;return n(t,i)})),r()(t=this.iframesToOverlays).call(t,(e=>{let{overlay:t,iframe:i}=e;return n(t,i)})),r()(i=this.videosToOverlays).call(i,(e=>{let{overlay:t,video:i}=e;return n(t,i)}))}),500)}clearOverlaysResizeIntervalChecker(){try{clearInterval(this.overlaysResizeIntervalChecker)}catch(e){}}#re(){const e=document.createElement("a");return e.setAttribute("href",this.adUrl),e.setAttribute("target","_blank"),e.setAttribute("rel","noopener noreferrer"),e.innerText="",e.addEventListener("click",(e=>{this.#i.debug("click on overlay is mobile no tabswap no capture"),e.stopPropagation(),this.mobileClickListener(e)})),e}#se(){const e=document.createElement("div");return e.addEventListener("mousedown",(e=>{this.#i.debug("mousedown on overlay"),this.desktopClickListener(e)}),this.#E),e.addEventListener("click",(e=>{this.#i.debug("click on overlay"),this.desktopClickListener(e)}),this.#E),e}#R(e){let t;const i=e===document.body;if(t=te&&i&&!this.isTabSwap?this.#re():this.#se(),i)t.id=Fe,t.style.top="0px",t.style.left="0px",t.style.width=`${window.innerWidth||document.documentElement.clientWidth||document.body.clientWidth}px`,t.style.height=`${window.innerHeight||document.documentElement.clientHeight||document.body.clientHeight}px`,t.style.position="fixed";else{const i=e.getBoundingClientRect();t.style.top=`${i.top+window.scrollY}px`,t.style.left=`${i.left+window.scrollX}px`,t.style.width=`${i.width}px`,t.style.height=`${i.height}px`,t.style.position="absolute",t.setAttribute(Ue,"")}return t.setAttribute(Be,this.#l),t.style.zIndex=this.#oe(e).toString(),t.style.backgroundColor="transparent",document.body.appendChild(t),t}attachVideoOverlays(){const e=document.querySelectorAll("video");for(let t=0;t<e.length;t++)this.elementTargeting.isActionAllowedOnElement(e[t])&&this.videosToOverlays.push({video:e[t],overlay:this.#R(e[t])})}attachIframeOverlays(){const e=document.querySelectorAll("iframe");for(let t=0;t<e.length;t++)this.elementTargeting.isActionAllowedOnElement(e[t])&&this.iframesToOverlays.push({iframe:e[t],overlay:this.#R(e[t])})}attachAnchorOverlays(){const e=document.querySelectorAll("a");for(let t=0;t<e.length;t++)this.elementTargeting.isActionAllowedOnElement(e[t])&&this.anchorsToOverlays.push({anchor:e[t],overlay:this.#R(e[t])})}clearVideoOverlays(){for(let e=0;e<this.videosToOverlays.length;e++)this.videosToOverlays[e].overlay.parentNode.removeChild(this.videosToOverlays[e].overlay),this.videosToOverlays[e].overlay=null;this.videosToOverlays.length=0}clearAnchorOverlays(){for(let e=0;e<this.anchorsToOverlays.length;e++)this.anchorsToOverlays[e].overlay.parentNode.removeChild(this.anchorsToOverlays[e].overlay),this.anchorsToOverlays[e].overlay=null;this.anchorsToOverlays.length=0}clearIframeOverlays(){for(let e=0;e<this.iframesToOverlays.length;e++)this.iframesToOverlays[e].overlay.parentNode.removeChild(this.iframesToOverlays[e].overlay),this.iframesToOverlays[e].overlay=null;this.iframesToOverlays.length=0}attachFullOverlay=()=>{const e=this.#R(document.body);if(H||(I(window,"resize",v()(Ke).call(Ke,{divOverlay:e,element:window})),I(document.body,"resize",v()(Ke).call(Ke,{divOverlay:e,element:window}))),this.fullOverlay=e,this.modifyBodyObserver)try{this.#ae()}catch(e){this.#i.error(e)}};clearFullOverlay(){this.#i.debug("clear full overlay"),this.fullOverlay?(this.modifyBodyObserver&&this.#ce(),H||(E(window,Ke),E(document.body,Ke)),this.fullOverlay.parentNode.removeChild(this.fullOverlay),this.fullOverlay=null):this.#i.debug("no overlay to clear")}reattachFullOverlay(){this.modifyBodyObserver=!1,this.clearFullOverlay(),this.attachFullOverlay(),this.modifyBodyObserver=!0}#oe(e){if(e!==document.body&&this.elementTargeting.isPresent()&&!this.elementTargeting.shouldTriggerPopOnTargetClick){const t=window.getComputedStyle(e);let i=A()(t.zIndex,10);return Qe()(i)?i=1:i+=1,i}return ze}#ae(){this.observer=new MutationObserver((e=>{for(let t=0;t<e.length;t++){const i=e[t];for(let e=0;e<i.addedNodes.length;e++)if(i.addedNodes[e].style&&A()(i.addedNodes[e].style.zIndex,10)>=1&&i.addedNodes[e].id!==Fe&&!i.addedNodes[e].hasAttribute("dontfo")&&!i.addedNodes[e].hasAttribute(Ue))return this.#i.debug("observed element",i.addedNodes[e],"with zIndex value larger or equal to our full body overlay. reattaching full body overlay"),void this.reattachFullOverlay()}})),this.observer.observe(document.documentElement,{attributes:!1,childList:!0,subtree:!0})}#ce(){this.observer&&this.observer.disconnect(),this.observer=null}},Ye=class{targetElementsCssSelector=null;shouldTriggerPopOnTargetClick=!1;#le=!1;constructor(e,t,i){this.targetElementsCssSelector=e,this.shouldTriggerPopOnTargetClick=t,this.zoneId=i}isPresent(){return!!this.targetElementsCssSelector}preventClickOnInterstitialAndBanner(){this.#le=!0}isActionAllowedOnElement(e){let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:[],i=arguments.length>2&&void 0!==arguments[2]?arguments[2]:[];if(e.hasAttribute(Be))return e.getAttribute(Be)===this.zoneId;if(e.hasAttribute("doskip"))return"1"===e.getAttribute(Ne)&&!this.#le;0===t.length&&(t=m()(document.querySelectorAll('[doskip*="1"]')));for(const i of t)if(i.contains(e))return"1"===e.getAttribute(Ne)&&!this.#le;if(this.isPresent()){0===i.length&&(i=document.querySelectorAll(this.targetElementsCssSelector));for(let t=0;t<i.length;t++)if(e===i[t])return this.shouldTriggerPopOnTargetClick;return!this.shouldTriggerPopOnTargetClick}return!0}},Xe=class{#s;#y=null;#t={};#P=!1;#$;#m=!1;#E=!0;#i;#x="52.5";#L=null;#de=12;#A=!1;constructor(e){var t,i;this.#i=new y(`suv5_${e.zoneId}`),this.#s=window[e.adcashGlobalName],e.tagVersionSuffix&&(this.#x+=e.tagVersionSuffix),this.#i.debug("tag version:",this.#x),this.#i.debug("init pop with config:",e),this.#t=e,this.elementTargeting=new Ye(this.#t.targetElementsCssSelector,this.#t.triggerOnTargetElementsClick,this.#t.zoneId),!te||this.elementTargeting.isPresent()||this.#t.linkedZoneId||(this.#E=!1),this.#i.debug("useCapture:",this.#E),this.overlays=new Je(this.elementTargeting,v()(t=this.#z).call(t,this),v()(i=this.#ue).call(i,this),this.#i,this.#t.zoneId,this.#E),this.#B(),this.localStorage=new qe(`suv5_${e.zoneId}_state`);const n=this.localStorage.getState();n&&n.adbExpiresAt>be()()&&this.#s.enableAdbMode();const r=be()();if(n&&n.renderAfterTimestamp>r){var s;const e=n.renderAfterTimestamp-r;this.#i.debug(`previous state present. bid after ${e/1e3} sec`),f()(v()(s=this.#he).call(s,this),e)}else this.#he()}async#T(){const e=await this.#s.getClientHints(!1);let t=`${window.location.protocol}//${this.#t.adserverDomain}/script/suurl5.php`;if(this.#t.adblockSettings&&this.#s.isAdbMode()){const{adserverDomain:e}=this.#t.adblockSettings,i=`/${ne("abcdefgh0123456789")}`;t=`${window.location.protocol}//${e}${i}`}if(t+=`?r=${this.#t.zoneId}`,this.#m&&(t+="&rbd=1"),this.#t.targetCountries){const e=this.#t.targetCountries.join(",");this.#t.triggerOnTargetCountries?t+="&allowed_countries="+encodeURIComponent(e):t+="&excluded_countries="+encodeURIComponent(e)}return t=t+e+"&cbur="+Math.random()+"&cbiframe="+$()+"&cbWidth="+F()+"&cbHeight="+U()+"&cbtitle="+encodeURIComponent(B())+"&cbpage="+encodeURIComponent(P())+"&cbref="+encodeURIComponent(N())+"&cbdescription="+encodeURIComponent(j("description"))+"&cbkeywords="+encodeURIComponent(j("keywords"))+"&cbcdn="+encodeURIComponent(this.#s.getCdnDomain())+"&ufp="+encodeURIComponent(this.#t.uniqueFingerprint)+"&ts="+be()()+"&srs="+this.#s.getSesionRandomString()+"&atv="+this.#x,this.#t.sub1&&(t+=`&sub1=${encodeURIComponent(this.#t.sub1)}`),this.#t.sub2&&(t+=`&sub2=${encodeURIComponent(this.#t.sub2)}`),this.#t.publisherUrl&&(t+=`&pu=${encodeURIComponent(this.#t.publisherUrl)}`),this.#t.storeUrl&&(t+=`&storeurl=${encodeURIComponent(this.#t.storeUrl)}`),this.#t.c1&&(t+=`&c1=${encodeURIComponent(this.#t.c1)}`),this.#t.c2&&(t+=`&c2=${encodeURIComponent(this.#t.c2)}`),this.#t.c3&&(t+=`&c3=${encodeURIComponent(this.#t.c3)}`),this.#t.pubHash&&(t+=`&pub_hash=${encodeURIComponent(this.#t.pubHash)}`),this.#t.pubClickId&&(t+=`&pub_clickid=${encodeURIComponent(this.#t.pubClickId)}`),this.#t.pubValue&&(t+=`&pub_value=${encodeURIComponent(this.#t.pubValue)}`),this.#t.fallbackOn&&(t+=`&fallbackon=${encodeURIComponent(this.#t.fallbackOn)}`),this.#t.adblockSettings&&(t+="&abtg=1"),this.#t.isAutoTag&&(t+="&atag=1"),this.#t.aggressivity&&(t+=`&aggr=${this.#t.aggressivity}`),this.#t.collectiveZoneId&&(t+=`&czid=${this.#t.collectiveZoneId}`),this.#t.recordPageView&&(t+="&ppv=1"),this.#t.linkedZoneId&&(t+=`&pblcz=${this.#t.linkedZoneId}`),this.#t.abTest&&(t+=`&ab_test=${this.#t.abTest}`),this.#t.adblockSettings&&this.#t.adblockSettings.adbVersion&&(t+=`&adbv=${this.#t.adblockSettings.adbVersion}`),this.#t.adblockSettings&&this.#s.isAdbMode()?(t+="&sadbl=2",t+="&fmt=suv5",this.#i.debug(`bid url: ${t}`),re(t)):(this.#i.debug(`bid url: ${t}`),t)}#U(e){try{let t=this.#L?this.#L(""):window.open("");return t.document.open(),t.document.writeln('<meta name="referrer" content="no-referrer"><script type="text/javascript">window.location = "'+e+'";<\/script>'),t.document.close(),t}catch(e){return this.#i.error("window open failed:",e),null}}#B(){var e;if(document.body){var t;const e=document.createElement("iframe");return e.width="0",e.height="0",e.tabindex="-1",e.style="position:absolute;top:-1000px;left:-1000px;visibility:hidden;border:medium none;background-color:transparent;",document.body.appendChild(e),void(this.#L=v()(t=e.contentWindow.open).call(t,e.contentWindow))}f()(v()(e=this.#B).call(e,this),50)}#ge(){var e;document.body?(this.overlays.isTabSwap=this.#M(),this.overlays.adUrl=this.#y.url,this.#y.preventClick&&(this.#i.debug("prevent triggering when clicking on banner/interstitial"),this.elementTargeting.preventClickOnInterstitialAndBanner()),this.elementTargeting.isPresent()||this.#y.preventClick?(te?(this.#i.debug("ismob. attach v,i and a overlays"),this.overlays.attachIframeOverlays(),this.overlays.attachVideoOverlays()):(this.#i.debug("isdesk. attach i overlays only"),this.overlays.attachIframeOverlays(),this.overlays.attachVideoOverlays()),this.overlays.setOverlaysResizeIntervalChecker()):this.#t.linkedZoneId?this.#i.debug("liked zone present. dont attach full overlay"):this.tryToAttachFullOverlay(),this.#j(),this.#i.debug("ready to show ad")):f()(v()(e=this.#ge).call(e,this),100)}tryToAttachFullOverlay(){var e;this.#y&&!this.#P&&(document.getElementById(Fe)?f()(v()(e=this.tryToAttachFullOverlay).call(e,this),100):this.overlays.attachFullOverlay())}#fe(){return this.#t.refreshRate?this.#t.refreshRate:this.#y.refreshRate}#pe(){this.#de<7200&&(this.#de*=5)}#ve(){this.#de>12&&(this.#de=12)}async#he(){var e;this.#y=null,this.#$=null,this.#P=!1;const t=await this.#T();let i;try{i=await fetch(t)}catch(e){var n;return this.#t.adblockSettings&&!this.#A?(this.#i.debug("fetch failed: try alt domain and path"),this.#A=!0,this.#s.enableAdbMode(),void this.#he()):this.#s.isAdbMode()?void this.#i.debug("fetch failed: alt domain and path blocked. exit"):(this.#i.error(`unhandled error: ${e.message}. Try again after 30 seconds`),void f()(v()(n=this.#he).call(n,this),3e4))}if(204===i.status)return this.#i.debug(`no inventory! try again after ${this.#de} seconds`),this.#m=!0,f()((()=>{this.#he()}),1e3*this.#de),void this.#pe();if(203!==i.status){if(202===i.status)return i=await i.json(),this.#i.debug(`capped! try again after ${i.capped_ttl} seconds`),this.#m=!0,void f()((()=>{this.#he()}),1e3*i.capped_ttl);if(200!==i.status)this.#i.error(`unsupported res status: ${i.status}. try again after 30 seconds`),f()(v()(e=this.#he).call(e,this),3e4);else{if(i=await i.json(),this.#ve(),this.#y={url:this.#N(i.url),impressionUrl:i.iurl,refreshRate:i.refreshRate,delay:i.delay,type:i.type,checkTimeout:i.checkTimeout,preventClick:i.preventClick},i.targetElementsCssSelector&&!this.elementTargeting.targetElementsCssSelector&&(this.elementTargeting.targetElementsCssSelector=i.targetElementsCssSelector,this.elementTargeting.shouldTriggerPopOnTargetClick=i.triggerOnTargetElementsClick),!this.#m){const e=this.#t.delay??i.delay??0;return this.#i.debug("delay is",e),void(e>0?f()((()=>{this.#ge()}),1e3*e):this.#ge())}this.#ge()}}else this.#i.debug("fallback detected. exit")}#N(e){let t=e;return D&&W<59||_&&W<56?t='data:text/html;charset=utf-8, <html><meta http-equiv="refresh" content="0;URL='+e+'"></html>':G&&D&&!M&&W>63&&(e="googlechrome://"+e.replace(/(^\w+:|^)\/\//,"")),t}#z(e){if(this.#i.debug(`showAdClickListener triggered by event type ${e.type} on ${e.target.tagName}`),!e.isTrusted)return void this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: event is not trusted`);if(!this.#y)return void this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: current pop has no ad loaded`);if(this.#P)return void this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: current pop is locked`);if(this.#s.isShowingPop)return void this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: another pop is being currently shown`);const t=m()(document.querySelectorAll('[doskip*="1"]'));let i=[];if(this.elementTargeting.isPresent()){i=document.querySelectorAll(this.elementTargeting.targetElementsCssSelector),this.#i.debug("event coordinates:",e.clientX,e.clientY);const n=document.elementsFromPoint(e.clientX,e.clientY);let r=!1;for(let s=0;s<n.length;s++){const o=this.elementTargeting.isActionAllowedOnElement(n[s],t,i);if(this.elementTargeting.shouldTriggerPopOnTargetClick&&o){r=!0;break}if(!this.elementTargeting.shouldTriggerPopOnTargetClick&&!o)return void this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: action not allowed - click on area with bl element`,e.target)}if(this.elementTargeting.shouldTriggerPopOnTargetClick&&!r)return void this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: action not allowed - click on area with no wl element`,e.target)}else if(!this.elementTargeting.isActionAllowedOnElement(e.target,t,i))return void this.#i.debug(`${e.type} on ${e.target.tagName}: pop rejected: action not allowed on element`,e.target);if(this.#s.isShowingPop=!0,this.#P=!0,e.stopPropagation(),e.preventDefault(),this.#i.debug(`${e.type} on ${e.target.tagName}: triggering pop`),this.#M())this.#H();else{if(te)return this.#$=!0,void ye().all([this.#D(),new(ye())((e=>{this.#L?e(this.#L(this.#y.url,"_blank","noopener,noreferrer")):e(window.open(this.#y.url,"_blank","noopener,noreferrer"))}))]).then((()=>{this.#be()}));this.#L?this.#L(this.#y.url,"_blank","noopener,noreferrer"):window.open(this.#y.url,"_blank","noopener,noreferrer"),f()((()=>{this.#$="hidden"===document.visibilityState||!document.hasFocus(),this.#D().finally((()=>{this.#be()}))}),100)}}#ue(e){this.#i.debug(`showAdMobileClickListener triggered by event type ${e.type} on`,e.target.tagName),e.isTrusted?this.#y?this.#P?this.#i.debug("pop rejected: current pop is locked"):this.#s.isShowingPop?this.#i.debug("pop rejected: another pop is being currently shown"):this.elementTargeting.isActionAllowedOnElement(e.target)?(this.#s.isShowingPop=!0,this.#P=!0,this.#i.debug("triggering pop"),this.#$=!0,this.#D().finally((()=>{this.#be()}))):this.#i.debug("pop rejected: action not allowed on element",e.target):this.#i.debug("pop rejected: current pop has no ad loaded"):this.#i.debug("pop rejected: event is not trusted")}async#D(){let e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:0;const t=await this.#s.getClientHints(!1);this.#i.debug("window opened:",this.#$);let i=this.#y.impressionUrl+"&wo="+(this.#$?"1":"0");if(window["utsid-send"]&&(i+=`&utsid=${window["utsid-send"]}`),e>0&&(this.#i.debug(`retry impression. Attempt ${e}`),i+=`&rtry=${e}`),i=i+t+"&cbpage="+encodeURIComponent(P())+"&cbref="+encodeURIComponent(N()),this.#i.debug("send impression. url:",i),se){this.#i.debug("keepalive supported!");let t=null,n=!1;try{t=await fetch(i,{keepalive:!0})}catch(e){if(this.#i.error(e),this.#t.adblockSettings&&!this.#s.isAdbMode())return this.#i.debug("imp failed: try alt domain and path"),void this.#s.enableAdbMode();n=!0}if(t&&!t.ok||n)return void(e<4&&(await this.#D(e+1),document.dispatchEvent(new CustomEvent("impression-retry-event"))))}else navigator.sendBeacon?(this.#i.debug("keepalive NOT supported! use sendBeacon"),navigator.sendBeacon(i)):(this.#i.debug("keepalive NOT supported! use image.src"),(new Image).src=i);document.dispatchEvent(new CustomEvent("impression-event"))}#be(){this.elementTargeting.isPresent()?te?(this.#i.debug("ismob. clear v,i and a overlays"),this.overlays.clearOverlaysResizeIntervalChecker(),this.overlays.clearIframeOverlays(),this.overlays.clearVideoOverlays()):(this.#i.debug("isdesk. clear i overlays only"),this.overlays.clearIframeOverlays(),this.overlays.clearVideoOverlays()):this.#t.linkedZoneId||this.overlays.clearFullOverlay(),this.#V(),this.#s.isShowingPop=!1;const e=this.#t.refreshRate??this.#y.refreshRate;this.#i.debug("refreshRate time is",e),this.#y=null,e&&e>0&&f()((()=>{this.#i.debug("refreshRate time has passed. Rebid"),this.#m=!0,this.#he()}),1e3*e)}#M(){return"type"in this.#y&&"tabswap"===this.#y.type}#H(){this.#i.debug("do tabswap"),this.localStorage.setState({renderAfterTimestamp:be()()+1e3*this.#fe(),adbExpiresAt:this.#s.isAdbMode()?be()()+Ve:0});const e=this.#y.url;this.#L?this.#L(window.location.href,"_blank","noreferrer"):window.open(window.location.href,"_blank","noreferrer"),this.#$=!0,this.#D().finally((()=>{f()((()=>{const t=document.createElement("a");t.href=e,t.rel="noopener noreferrer",document.body.appendChild(t),t.click(),document.body.removeChild(t)}),50)}))}#j(){var e;const t={zoneId:this.#t.zoneId,callback:v()(e=this.#z).call(e,this)};te&&ie&&(this.#i.debug("subscribe to scroll"),this.#s.subscribe("scroll",t)),te||(this.#i.debug("subscribe to mousedown"),this.#s.subscribe("mousedown",t,this.#E)),this.#i.debug("subscribe to click"),this.#s.subscribe("click",t,this.#E)}#V(){te&&ie&&(this.#i.debug("unsubscribe from scroll"),this.#s.unsubscribe("scroll",this.#t.zoneId)),te||(this.#i.debug("unsubscribe from mousedown"),this.#s.unsubscribe("mousedown",this.#t.zoneId,this.#E)),this.#i.debug("unsubscribe from click"),this.#s.unsubscribe("click",this.#t.zoneId,this.#E)}},et=i(2243),tt=i.n(et),it=class{#t={};#i=null;#n=0;#r;#s;#o;constructor(e,t,i,n,r){this.#t=e,this.#i=i,this.#n=0,this.#r=t,this.#s=n,this.#o=r}render(e){let t=null;switch(e.type){case 1:this.#i.debug(`rendering INTERSTITIAL IFRAME (type 1) in ${this.#t.isOverlay?"OVERLAY":"FULLSCREEN"} mode`),t=this.#t.isOverlay?Te(e.url):Re(e.url);break;case 3:this.#i.debug(`rendering INTERSTITIAL IMAGE (type 3) in ${this.#t.isOverlay?"OVERLAY":"FULLSCREEN"} mode`),t=this.#t.isOverlay?Oe(e.url,e.ad.url,e.ad.width,e.ad.height):Pe(e.url,e.ad.url,e.ad.width,e.ad.height);break;case 4:if(e.isHtmlTemplate)return this.#i.debug("rendering INTERSTITIAL HTML CUSTOM (type 4)"),void this.#a(e);this.#i.debug(`rendering INTERSTITIAL HTML (type 4) in ${this.#t.isOverlay?"OVERLAY":"FULLSCREEN"} mode`),t=this.#t.isOverlay?Ie(Ne):$e(Ne);break;default:return void this.#i.error(`no such type of interstitial: ${e.type}`)}const i=document.createElement("div");document.body.appendChild(i);const n=i.attachShadow({mode:"open"}),r=this.#t.isOverlay?Ce:Ee;if(n.appendChild(r(this.#t.texts.goToButton,e.url,this.#c(),t.content,e.iurl)),4===e.type){const t=n.getElementById("creative_iframe");t.contentWindow.contents=e.html,t.src='javascript:window["contents"]'}if(!this.#t.disableCountdown&&this.#t.moveTimerInsideButtonAfter>0){this.#n=this.#t.moveTimerInsideButtonAfter,n.getElementById("closeButton").innerHTML=this.#c();const e=d()((()=>{this.#n--,n.getElementById("closeButton").innerHTML=this.#c(),0===this.#n&&clearInterval(e)}),1e3)}n.getElementById("closeButton").addEventListener("click",(()=>{this.#n>0||(this.#i.debug("close button click. remove modal host, resize listener if present and do callback"),i.remove(),t.resizeFunc&&window.removeEventListener("resize",t.resizeFunc),this.#r())}))}#c(){let e=`${this.#t.texts.pleaseWait}: ${this.#n} ${this.#t.texts.timePlural}`;return 1===this.#n&&(e=`${this.#t.texts.pleaseWait}: ${this.#n} ${this.#t.texts.timeSingle}`),0===this.#n&&(e=this.#t.disableCountdown?this.#t.texts.xLabel:this.#t.texts.skipAd),e}#a(e){const t=(new DOMParser).parseFromString(e.html,"text/html").querySelector("script"),i=document.createElement("script");i.style.zIndex="2147483646",t.src?i.setAttribute("src",t.src):i.innerText=t.innerText;const n=()=>{this.#i.debug("CT-CLICK"),fetch(e.link,{mode:"no-cors"}),E(document,"ct-click",n)},r=()=>{this.#i.debug("CT-CLOSE"),E(document,"ct-click",n),E(document,"ct-close",r),document.body.removeChild(i),this.#r()};I(document,"ct-click",n),I(document,"ct-close",r);let s=e.iurl;window[Se]&&(s+=`&utsid=${window[Se]}`),i.onload=async()=>{try{await fetch(s.toString())}catch(e){return this.#i.debug(e),void(this.#o&&!this.#s.isAdbMode()&&(this.#i.debug("imp failed: try alt domain and path"),this.#s.enableAdbMode()))}document.dispatchEvent(new CustomEvent("impression-event"))},i.onerror=()=>{this.#i.debug("custom html script failed to load"),this.#r(xe)},document.body.appendChild(i)}},nt=class{#l;#me;#ye;#u;#h;#g;#p;#s;#v;#o;#i;#m=!1;#t={};#b;#y=null;#w=12;#x="52.5";#k=null;#we=!1;#xe="";#S=!1;#C;constructor(e){this.#i=new y(`interstitial_${e.zoneId}`),this.#i.debug("init interstitial with config:",e),this.#l=e.zoneId,this.#ye=e.isAutoTag,this.#u=e.collectiveZoneId,this.#h=e.aggressivity,this.#g=e.recordPageView,this.#p=e.abTest,this.#s=window[e.adcashGlobalName],this.#v=e.adserverDomain,this.#o=e.adblockSettings,this.#me=e.sub1,this.#S=e.isLoadedAsPartOfLibrary,this.#C=e.uniqueFingerprint,e.tagVersionSuffix&&(this.#x+=e.tagVersionSuffix),this.#s.getClientHints(!1).then((e=>{this.#b=e,this.#he()}))}async#he(){const e=this.#T();let t;try{t=await fetch(e)}catch(e){if(this.#i.error(e),this.#o&&!this.#s.isAdbMode())return this.#i.debug("fetch call failed. Switch to adblck domain and path"),this.#s.enableAdbMode(),void this.#he()}var i,n,r,s;return 204===t.status?(this.#i.debug(`no inventory! try bidding again after ${this.#w} sec`),f()(v()(i=this.#he).call(i,this),1e3*this.#w),void(this.#w<7200&&(this.#w*=5))):(200!==t.status&&202!==t.status||(t=await t.json(),this.#i.debug("response:",t)),this.#w=12,t.hp&&this.#ke(t.hp),t.capped_ttl?(this.#i.debug(`capped! try bidding again after ${t.capped_ttl} sec`),void f()(v()(n=this.#he).call(n,this),1e3*t.capped_ttl)):t.fallback?(this.#i.debug("render fallback and exit"),void this.#Ae(t.fallback)):(this.#m?this.#y=t:(this.#i.debug("initial request. configure"),this.#t={moveTimerInsideButtonAfter:t.moveTimerInsideButtonAfter,delay:t.delay,refreshRate:t.refreshRate,isOverlay:t.isOverlay,disableCountdown:t.disableCountdown,texts:t.texts,showOnInnerLinkClick:t.showOnInnerLinkClick},this.#y=t.adPayload,this.#k=new it(this.#t,v()(r=this.#r).call(r,this),this.#i,this.#s,this.#o)),this.#b&&(this.#y.url+=this.#b,this.#y.iurl+=this.#b),4===this.#y.type&&this.#y.html&&(this.#y.html=`<!DOCTYPE html><html><head><meta name="referrer" content="no-referrer"></head><body>${this.#y.html}</body></html>`),void(!this.#m&&this.#t.delay>0?(this.#i.debug(`delay present. render after: ${this.#t.delay} sec`),f()(v()(s=this.#O).call(s,this),1e3*this.#t.delay)):this.#O())))}#Ae(e){this.#i.debug("fallback script str:",e);const t=(new DOMParser).parseFromString(e,"text/html").querySelector("script");if(!t)return void this.#i.error("invalid fallback script. move on");this.#i.debug("fallback script:",t);const i=document.createElement("script");for(const e of t.attributes)i.setAttribute(e.name,e.value);i.src||(i.textContent=t.textContent),document.body.appendChild(i)}#ke(e){const t=JSON.parse(atob(e));this.#i.debug("hp data:",t);const i={zoneId:t.pop_zone_id.toString(),linkedZoneId:t.source_zone_id.toString()};var n;t.attributes&&(t.attributes["element-list"]&&(i.targetElementsCssSelector=t.attributes["element-list"],i.triggerOnTargetElementsClick="allow"===t.attributes["element-action"]),t.attributes["country-list"]&&(i.targetCountries=tt()(n=t.attributes["country-list"]).call(n).split(","),i.triggerOnTargetCountries="allow"===t.attributes["country-action"])),this.#s.runPop(i)}#r(){if(this.#t.showOnInnerLinkClick&&this.#xe)return this.#i.debug("redirect to inner link"),void(window.location.href=this.#xe);this.#we=!1,this.#t.refreshRate>0?(this.#i.debug(`rebid after ${this.#t.refreshRate} sec`),f()((()=>{this.#m=!0,this.#he()}),1e3*this.#t.refreshRate)):this.#i.debug("no rebidding. finish")}#Se(){const e=document.querySelectorAll("a"),t=new(c())(P()).hostname;for(let i=0;i<e.length;i++)"href"in e[i]&&new(c())(e[i].href).hostname===t&&e[i].addEventListener("click",(t=>{t.stopPropagation?t.stopPropagation():t.cancelBubble=!0,t.preventDefault?t.preventDefault():t.returnValue=!1,this.#we||(this.#i.debug("click on inner link detected. render ad"),this.#we=!0,this.#xe=e[i].href,this.#k.render(this.#y))}),{capture:!0})}#O(){this.#i.debug("render"),this.#t.showOnInnerLinkClick?(this.#i.debug("google friendly interstitial. ad will be rendered on inner link click"),this.#Se()):this.#k.render(this.#y)}#T(){let e=`${window.location.protocol}//${this.#v}/script/interstitial.php`;if(this.#o&&this.#s.isAdbMode()){const{adserverDomain:t}=this.#o,i=`/${ne("abcdefgh0123456789")}`;e=`${window.location.protocol}//${t}${i}`}return e+=`?r=${this.#l}`,this.#m&&(e+="&rbd=1"),this.#b&&(e+=this.#b),e=e+`&srs=${this.#s.getSesionRandomString()}`+`&ufp=${encodeURIComponent(this.#C)}`+`&cbpage=${encodeURIComponent(P())}`+`&atv=${this.#x}`+`&cbref=${encodeURIComponent(N())}`,this.#me&&(e+=`&sub1=${encodeURIComponent(this.#me)}`),this.#ye&&(e+="&atag=1"),this.#u&&(e+=`&czid=${this.#u}`),this.#h&&(e+=`&aggr=${this.#h}`),this.#o&&(e+="&abtg=1"),this.#g&&(e+="&ppv=1"),this.#p&&(e+=`&ab_test=${this.#p}`),this.#o&&this.#o.adbVersion&&(e+=`&adbv=${this.#o.adbVersion}`),this.#o&&this.#s.isAdbMode()?(e+="&sadbl=2",e+="&fmt=intrn",this.#i.debug(`bid url: ${e}`),re(e)):(this.#i.debug(`bid url: ${e}`),e)}};const rt="#399afe",st="utsid-send";class ot extends HTMLElement{constructor(){super(),this._shadowRoot=this.attachShadow({mode:"open"}),this.click=e=>{e.stopPropagation();const t=document.createEvent("Event");t.initEvent("inpageclick",!0,!0),this.dispatchEvent(t)},this.close=e=>{e.stopPropagation();const t=document.createEvent("Event");t.initEvent("inpageclose",!0,!0),this.dispatchEvent(t),document.dispatchEvent(new CustomEvent("in-page-closed"))},this.missclick=()=>{document.dispatchEvent(new CustomEvent("in-page-missclick"))}}connectedCallback(){const e=document.querySelectorAll("in-page-message");let t=0,i="top";for(let i=0;i<e.length;i++)e[i].shadowRoot.childNodes[3]&&e[i].shadowRoot.childNodes[3].offsetHeight&&(t+=e[i].shadowRoot.childNodes[3].offsetHeight);const n=A()(this.getAttribute("data-offset-top"),10),r=this.getAttribute("data-render-pos-desktop"),s=this.getAttribute("data-render-pos-mobile");n?t+=n:i=te?s:r;const o={closeButtonStyle:"",id:this.getAttribute("id"),position:i,offset:t,dataTitle:this.getAttribute("data-title"),dataDescription:this.getAttribute("data-description"),dataIcon:this.getAttribute("data-icon"),notePaddingRightStyleRaw:"",widthOfMissclickArea:50};var a;this.shadowRoot.innerHTML=`\n        <style>\n            div[id^='note-'] {\n                font-family: -apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;\n                font-weight: 400;\n                font-size: 16px;\n                line-height: 1.3;\n                position: fixed !important;\n                right: 0;\n                /* pure-css */\n                letter-spacing: -0.31em;\n                text-rendering: optimizespeed;\n                display: -webkit-box;\n                display: -ms-flexbox;\n                display: flex;\n                -webkit-box-orient: horizontal;\n                -webkit-box-direction: normal;\n                -ms-flex-flow: row wrap;\n                flex-flow: row wrap;\n                -ms-flex-line-pack: start;\n                align-content: flex-start;\n                align-items: center;\n                cursor: pointer;\n                transition: padding-right 0.1s, top 0.3s;\n                overflow: hidden;\n                z-index: 2147483645;\n                word-wrap: break-word;\n                width: 380px;\n                padding-top: 20px;\n            }\n\n            .note-inner {        \n                margin: 5px;\n                border-radius: 55px;        \n                position: relative;\n                background: ${rt};\n                color: #ffffff !important;\n                width: 70%;\n                text-align: center;\n                height: 100px;\n                justify-content: center;\n                display: flex;\n                align-items: center;\n            }\n\n            div[id*='note-'] p, img.graph, div[id*='close-'] {\n                display: inline-block;\n                letter-spacing: normal;\n                word-spacing: normal;\n                vertical-align: middle;\n                text-rendering: auto;\n                text-align: center;        \n            }      \n\n            div[id*='note-'] p {\n                width: 90%;\n                padding: 2%;\n                font-size: 0.9em\n            }\n\n            /* BUBBLE IMAGE */\n            img.graph {\n                width: 76px;\n                height: 76px;    \n                box-sizing: border-box;\n                border-radius: 50%;          \n                position: relative;\n                margin-left: 2%;\n                border: 4px solid ${rt};\n            }\n\n            /* CLOSE BUTTON */\n            div[id^='close-'] {\n                font-size: 20px;\n                margin-top: 10px;\n                z-index: 23;\n                display: inline-block;\n                width: 24px;\n                height: 24px;\n                background: transparent;        \n                text-align: center;\n                color: #a6a0a7;\n            }\n\n            div[id^='close-']:hover {\n                background: #a0a0ff;\n            }\n\n            .impression {\n                display: none;\n                width: 0px;\n                height: 0px;\n            }\n\n            div[id*="missclick-"] {\n                right: 0;\n                top: 0;\n                height: 100%;\n                /*margin-top: -30px;*/\n                width: ${(a=o).widthOfMissclickArea}px;\n                z-index: 2;\n                position: absolute !important;\n                align-items: start;\n                justify-content: center;\n                display: flex;\n            }\n\n            @media all and (max-width: 380px) {\n                div[id*='note-'] {\n                    width: 100%;\n                }\n                \n                img.graph {\n                    margin-left: 2%;\n                }\n            }\n\n            ${a.closeButtonStyle}\n        </style>\n        \n        <div id="note-${a.id}" style="${a.position}:${a.offset}px;">\n          <div class="note-inner">\n            <p><b>${a.dataTitle}</b><br/>${a.dataDescription}</p>\n          </div>\n          <img class="graph" src="${a.dataIcon}" alt="graph">\n          <div id="missclick-${a.id}">\n            <div id="close-${a.id}">&#10005</div>          \n          </div>\n        </div>\n    `;const c=this.shadowRoot.getElementById(`note-${this.getAttribute("id")}`),l=this.shadowRoot.getElementById(`close-${this.getAttribute("id")}`),d=this.shadowRoot.getElementById(`missclick-${this.getAttribute("id")}`);if(this.hasAttribute("data-imp-link")){let e=this.getAttribute("data-imp-link");window[st]&&(e+=`&utsid=${window[st]}`),e+=`&cbpage=${encodeURIComponent(P())}`,e+=`&cbref=${encodeURIComponent(N())}`;const t=document.createElement("img");t.src=e.toString(),t.setAttribute("class","impression"),c.appendChild(t)}I(c,"click",this.click),I(l,"click",this.close),I(d,"click",this.missclick)}}var at=ot;const ct=1e3;var lt=class{#t={};#i;#s;#b="";#Ce;#m=!1;#x="52.5";#Te=[];#Oe=null;#Ie=!0;#Ee;#A=!1;constructor(e){this.#i=new y(`ippg_new_${e.zoneId}`),this.#i.debug("init ippg with config:",e),this.#t=e,this.#s=window[e.adcashGlobalName],this.#Ee=this.#t.refreshRate,customElements.get("in-page-message")||customElements.define("in-page-message",at),this.#s.getClientHints(!1).then((e=>{this.#b=e,this.#he()}))}#T(){let e=`${window.location.protocol}//${this.#t.adserverDomain}/script/push.php`;if(this.#t.adblockSettings&&this.#s.isAdbMode()){const{adserverDomain:t}=this.#t.adblockSettings,i=`/${ne("abcdefgh0123456789")}`;e=`${window.location.protocol}//${t}${i}`}return e+=`?r=${this.#t.zoneId}&ipp=1`,this.#Ce=te?this.#t.renderPosMobile:this.#t.renderPosDesktop,e+=`&mads=${this.#t.maxAds}&position=${this.#Ce}`,this.#t.isAutoTag&&(e+=`&czid=${this.#t.collectiveZoneId}&atag=1`),this.#t.aggressivity&&(e+=`&aggr=${this.#t.aggressivity}`),this.#t.adblockSettings&&(e+="&abtg=1"),this.#m&&(e+="&rbd=1"),this.#t.recordPageView&&(e+="&ppv=1"),this.#t.abTest&&(e+=`&ab_test=${this.#t.abTest}`),this.#t.sub1&&(e+=`&sub1=${encodeURIComponent(this.#t.sub1)}`),this.#t.adblockSettings&&this.#t.adblockSettings.adbVersion&&(e+=`&adbv=${this.#t.adblockSettings.adbVersion}`),e=e+`&srs=${this.#s.getSesionRandomString()}`+`&ufp=${encodeURIComponent(this.#t.uniqueFingerprint)}`+`&cbpage=${encodeURIComponent(P())}`+`&atv=${this.#x}`+`&cbref=${encodeURIComponent(N())}`,this.#b&&(e+=this.#b),this.#Oe&&(e+="&ipptr=1"),this.#t.adblockSettings&&this.#s.isAdbMode()?(e+="&sadbl=2",e+="&fmt=ippg",this.#i.debug(`bid url: ${e}`),re(e)):(this.#i.debug(`bid url: ${e}`),e)}async#he(){var e;if(this.#Re()>=this.#t.maxAds||!this.#Ie||document.fullscreenElement||document.mozFullScreenElement||document.webkitFullscreenElement)return void(this.#t.refreshRate>0&&(this.#m=!0,f()(v()(e=this.#he).call(e,this),this.#Ee*ct)));let t;try{t=await fetch(this.#T())}catch(e){if(this.#i.error(e),this.#t.adblockSettings&&!this.#A)return this.#i.debug("fetch call failed. Switch to adblck domain and path"),this.#A=!0,this.#s.enableAdbMode(),void this.#he()}var i,n;if(204===t.status)return this.#i.debug("unsold invertory!"),void(this.#t.refreshRate>0&&(this.#i.debug(`refresh rate present. try bidding again after ${this.#Ee} sec`),this.#m=!0,f()(v()(i=this.#he).call(i,this),this.#Ee*ct),2*this.#Ee<1200&&(this.#Ee*=2)));if(200!==t.status&&202!==t.status||(this.#m=!0,t=await t.json(),this.#i.debug("response:",t)),t.fallback&&t.hp)return void this.#Ae(t.fallback);if(t.fallback)return void this.#Ae(t.fallback);if(t.hp,t.capped_ttl)return this.#i.debug(`capped! try bidding again after ${t.capped_ttl} sec`),void f()(v()(n=this.#he).call(n,this),t.capped_ttl*ct);this.#b&&(t.impression_url&&(t.impression_url+=this.#b),t.click_url&&(t.click_url+=this.#b));const r={type:t.type||1,script:t.script||"",title:t.title||"",description:t.description||"",icon:t.icon||t.image,link:t.click_url,impressionLink:t.impression_url||null,capped_ttl:A()(t.capped_ttl,10)||0};var s;this.#Ee=this.#t.refreshRate,2!==r.type||this.#Oe?(this.#Te.push(r),this.#Ie=!1,this.#Pe(),f()((()=>{this.#Ie=!0}),this.#Ee*ct)):(this.#Oe=r,this.#Ie=!1,await this.#$e(),f()((()=>{this.#Ie=!0}),this.#Ee*ct)),this.#t.refreshRate>0&&(this.#m=!0,f()(v()(s=this.#he).call(s,this),this.#Ee*ct))}#Re(){return this.#Oe?this.#Te.length+1:this.#Te.length}#Ae(e){this.#i.debug("fallback script str decoded:",e);const t=(new DOMParser).parseFromString(e,"text/html").querySelector("script");if(!t)return this.#i.error("invalid fallback script. move on"),null;this.#i.debug("fallback script:",t);const i=document.createElement("script");for(const e of t.attributes)i.setAttribute(e.name,e.value);i.src||(i.textContent=t.textContent),document.body.appendChild(i)}async#$e(){const e=(new DOMParser).parseFromString(this.#Oe.script,"text/html").querySelector("script"),t=document.createElement("script");e.src?t.setAttribute("src",e.src):t.innerText=e.innerText;const i=()=>{var e;this.#i.debug("CT-CLICK"),fetch(this.#Oe.link,{mode:"no-cors"}),document.removeEventListener("ct-click",i),f()(v()(e=this.#he).call(e,this),1e3)},n=()=>{this.#i.debug("CT-CLOSE"),document.removeEventListener("ct-click",i),document.removeEventListener("ct-close",n),this.#Oe=null,document.body.removeChild(t)};I(document,"ct-click",i),I(document,"ct-close",n);let r=this.#Oe.impressionLink;window[st]&&(r+=`&utsid=${window[st]}`),r+=`&cbpage=${encodeURIComponent(P())}`,r+=`&cbref=${encodeURIComponent(N())}`,t.onload=async()=>{try{await fetch(r.toString())}catch(e){return this.#i.debug(e),void(this.#t.adblockSettings&&!this.#s.isAdbMode()&&(this.#i.debug("imp failed: try alt domain and path"),this.#s.enableAdbMode()))}document.dispatchEvent(new CustomEvent("impression-event"))},t.onerror=()=>{this.#i.debug("custom html script failed to load"),this.#Oe=null},document.body.appendChild(t)}#Pe(){var e;this.#i.debug("drawing..");const t=document.querySelectorAll("in-page-message");if(t.length>0)for(let e=0;e<t.length;e++)t[e].remove();r()(e=this.#Te).call(e,((e,t)=>{const i=document.createElement("in-page-message");i.setAttribute("doskip","1"),i.setAttribute("id",t.toString()),i.setAttribute("data-icon",e.icon),i.setAttribute("data-title",e.title),i.setAttribute("data-description",e.description),i.setAttribute("data-offset-top",this.#t.offsetTop),i.setAttribute("data-render-pos-desktop",this.#t.renderPosDesktop),i.setAttribute("data-render-pos-mobile",this.#t.renderPosMobile),e.impressionLink&&(i.setAttribute("data-imp-link",e.impressionLink),e.impressionLink=null,document.dispatchEvent(new CustomEvent("impression-event"))),i.addEventListener("inpageclick",(()=>{var n;if(te||this.#t.adblockSettings&&this.#s.isAdbMode()){const t=document.createElement("a");t.href=e.link,t.rel="noopener, noreferrer",t.target="_blank",t.click()}else try{window.open(e.link,"_blank","noopener,noreferrer")}catch{}i.remove(),h()(n=this.#Te).call(n,t,1),this.#Pe()})),i.addEventListener("inpageclose",(()=>{var e;i.remove(),h()(e=this.#Te).call(e,t,1),this.#Pe()})),document.body.appendChild(i)}))}},dt=i(111),ut=i.n(dt),ht=i(8607),gt=i.n(ht),ft=class{#s;#t={};#i;#Le="";#ze;#l=null;#Fe=null;#Ue=null;#Be=null;#Ne;#je;#v="youradexchange.com";#Me="velocecdn.com";#He=!1;#De;#o;#A=!1;#x="52.5";constructor(e){this.#i=new y(`banner_${e.zoneId}`),this.#s=window[e.adcashGlobalName],this.#i.debug("init banner with config:",e),this.#t=e,this.#l=this.#t.zoneId,this.#Fe=this.#t.width,this.#Ue=this.#t.height,this.#Be=this.#t.renderIn,this.#o=this.#t.adblockSettings,this.#t.currentScript&&(this.#De=this.#t.currentScript),this.#Ne=this.#je=document.documentElement.clientWidth||document.body.clientWidth||window.innerWidth,e.tagVersionSuffix&&(this.#x+=e.tagVersionSuffix),this.#i.debug("tag version:",this.#x),this.#_e()}#Ve(){const e=this.#ze.impression_url;(new Image).src=e}async#_e(){this.#i.debug("get initial ad and config"),this.#Le=await R(this.#i);const e=await this.#We();let t;this.#i.debug("URL to fetch",e);try{t=await fetch(e)}catch(e){return this.#i.error(e),this.#o&&!this.#A?(this.#i.debug("fetch failed: try alt domain and path"),this.#A=!0,this.#s.enableAdbMode(),void this.#_e()):this.#s.isAdbMode()?void this.#i.debug("fetch failed: alt domain and path blocked. exit"):void this.#i.debug("fetch failed. exit")}200===t.status||202===t.status?(this.#i.debug("initial fetch received 200 or 202"),this.#ze=await t.json(),this.#qe()):204===t.status&&this.#i.debug("initial fetch received 204. No inventory")}async#We(){let e=`${window.location.protocol}//${this.#v}/script/banner.php`;if(this.#o&&this.#s.isAdbMode()){const{adserverDomain:t}=this.#o,i=`/${ne("abcdefgh0123456789")}`;e=`${window.location.protocol}//${t}${i}`}return e+=`?r=${this.#l}`,e+=`&cbpage=${encodeURIComponent(P())}`,e+=`&cbref=${encodeURIComponent(N())}`,e+=`&cbdescription=${encodeURIComponent(j("description"))}`,e+=`&cbkeywords=${encodeURIComponent(j("keywords"))}`,e+=`&cbtitle=${encodeURIComponent(B())}`,e+=`&srs=${z()}`,e+=`&ufp=${encodeURIComponent(this.#t.uniqueFingerprint)}`,e+=`&atv=${this.#x}`,this.#t.sub1&&(e+=`&sub1=${encodeURIComponent(this.#t.sub1)}`),this.#o&&this.#s.isAdbMode()?(e+="&sadbl=2",e+="&fmt=bnr",re(e)):e}#qe(){if(!this.#ze||"undefined"===this.#ze)return;if(this.#ze.hp&&(this.#Ge(this.#ze.hp),1===ut()(this.#ze).length))return;let e;e=this.#Be?document.querySelector(this.#Be):this.#t.currentElement?this.#t.currentElement:this.#De.parentElement,this.#Ze(e);const t=this.#Qe();e.appendChild(t)}#Qe(){let e;return this.#ze.fallback?(this.#i.debug("Banner type - fallback"),e=this.#Ke()):1===this.#ze.render_image?(this.#i.debug("Banner type - image"),e=this.#Je()):(this.#i.debug("Banner type - html"),e=this.#Ye()),this.#ze.fallback||this.#Ve(),this.#s||this.#Xe(),e}#Je(){const e=document.createElement("a");e.href=this.#ze.click_url,e.target="_blank",e.rel="noopener, noreferrer",e.style.display="block",e.style.width=`${this.#Fe?this.#Fe:this.#ze.width}px`,e.style.height=`${this.#Ue?this.#Ue:this.#ze.height}px`,e.style.position="relative",e.style.top=0,e.style.left=0,e.style.right=0,e.style.bottom=0,e.setAttribute("doskip","1"),e.setAttribute(Ne,"1");const t=document.createElement("img");if(t.src=this.#ze.image_url,t.target="_blank",t.width=this.#Fe?this.#Fe:this.#ze.width,t.height=this.#Ue?this.#Ue:this.#ze.height,this.#ze.width>this.#Ne&&this.#ze.force_resize){const i=(this.#Fe?this.#Fe:this.#ze.width)/this.#je;e.style.width=`${this.#je}px`,e.style.height=`${Math.round((this.#Ue?this.#Ue:this.#ze.height)/i)}px`,t.style="max-width: 100%;",t.width=this.#je,t.height=Math.round((this.#Ue?this.#Ue:this.#ze.height)/i)}return e.appendChild(t),e}#Ye(){const e=`banner_${this.#l}`,t=document.createElement("div");t.id=e,t.style.display="block",t.style.width=`${this.#Fe?this.#Fe:this.#ze.width}px`,t.style.height=`${this.#Ue?this.#Ue:this.#ze.height}px`,t.style.position="relative",t.style.top="0",t.style.left="0",t.style.right="0",t.style.bottom="0",t.width=this.#Fe?this.#Fe:this.#ze.width,t.height=this.#Ue?this.#Ue:this.#ze.height,t.setAttribute("doskip","1"),t.setAttribute(Ne,"1"),this.#et(t,this.#ze.html);const i=()=>{this.#i.debug("click recorded:",this.#ze.click_url),(new Image).src=this.#ze.click_url};return t.addEventListener("click",(()=>{this.#i.debug("click on divNode"),i()})),d()((()=>{document.activeElement&&"IFRAME"===document.activeElement.tagName&&((e,t)=>{let i=e.parentElement;for(;i;){if(i.id===t)return i;i=i.parentElement}return null})(document.activeElement,e)?this.#He||(this.#He=!0,this.#i.debug("click on iframe"),i()):this.#He=!1}),200),t}#et(e,t){var i;e.innerHTML=t,r()(i=m()(e.querySelectorAll("script"))).call(i,(e=>{var t;const i=document.createElement("script");r()(t=m()(e.attributes)).call(t,(e=>{i.setAttribute(e.name,e.value)}));const n=document.createTextNode(e.innerHTML);i.appendChild(n),e.parentNode.replaceChild(i,e)}))}#Ke(){const e=`banner_${this.#l}`,t=document.createElement("iframe");return t.id=e,t.style.border="medium none",t.style.padding="0",t.style.margin="0",t.style.width=`${this.#Fe?this.#Fe:this.#ze.width}px`,t.style.height=`${this.#Ue?this.#Ue:this.#ze.height}px`,t.width=this.#Fe?this.#Fe:this.#ze.width,t.height=this.#Ue?this.#Ue:this.#ze.height,t.scrolling="no",t.vspace="0",t.hspace="0",t.allowtransparency="true",t.allowfullscreen="true",t.srcdoc=this.#ze.fallback,t}#Ge=e=>{const t=JSON.parse(atob(e));if(this.#s){const e={zoneId:t.pop_zone_id.toString(),linkedZoneId:t.source_zone_id.toString()};var i;return t.attributes&&(t.attributes["element-list"]&&(e.targetElementsCssSelector=t.attributes["element-list"],e.triggerOnTargetElementsClick="allow"===t.attributes["element-action"]),t.attributes["country-list"]&&(e.targetCountries=tt()(i=t.attributes["country-list"]).call(i).split(","),e.triggerOnTargetCountries="allow"===t.attributes["country-action"])),void this.#s.runPop(e)}const n=document.createElement("script");if(n.type="text/javascript",n.src=`//${this.#Me}/script/suv4.js`,n.setAttribute("zid",t.pop_zone_id),n.setAttribute("lpzi",t.source_zone_id),n.setAttribute("data-adel","lwsu"),n.setAttribute("adlm","ipvipplm"),t.attributes)for(const e in t.attributes)n.setAttribute(e,t.attributes[e]);document.body.appendChild(n)};#Ze(e){if(this.#i.debug("Initial viewport:",this.#Ne),this.#ze.width>this.#Ne&&this.#ze.force_resize){var t=window.getComputedStyle(e),i=gt()(t.paddingLeft),n=gt()(t.marginLeft);this.#je=e.clientWidth-i-n,this.#i.debug("Parent element width:",this.#je)}}#Xe(){const e=document.createElement("a");e.style.display="none",e.style.visibility="hidden",e.style.position="relative",e.style.left="-1000px",e.style.top="-1000px",e.href=this.#ze.bot_link,document.body.appendChild(e)}};const pt="x4G9Tq2Kw6R7v1Dy3P0B5N8Lc9M2zF",vt="adblock-settings",bt=(()=>{let e=document.currentScript;return e||(e=document.getElementById("aclib")),e||(e=document.getElementById("adcash-lib")),e})();let mt=null;var yt=class{#Me;#tt={pop:!1,autoTag:!1,inPagePush:!1,interstitial:!1};#it;#b;#nt=new(t());#i;#rt;#st={mousedown:[],click:[],touchstart:[]};#ot={mousedown:[],scroll:[],click:[],touchstart:[]};#v="youradexchange.com";#o=null;#at;#ct;#lt=!1;isShowingPop=!1;#C;constructor(){if(mt)return mt;mt=this,this.#i=new y("aclib_adbl"),window.addEventListener("mousedown",(e=>{var t;this.#i.debug("win mousedown with capture: in"),r()(t=this.#st.mousedown).call(t,(t=>{this.#i.debug("win mousedown with capture: calling observer"),t.callback(e)}))}),!0),window.addEventListener("mousedown",(e=>{var t;this.#i.debug("win mousedown: in"),r()(t=this.#ot.mousedown).call(t,(t=>{this.#i.debug("win mousedown: calling observer"),t.callback(e)}))}),!1),window.addEventListener("click",(e=>{var t;this.#i.debug("win click with capture: in"),r()(t=this.#st.click).call(t,(t=>{this.#i.debug("win click with capture: calling observer"),t.callback(e)}))}),!0),window.addEventListener("click",(e=>{var t;this.#i.debug("win click: in"),r()(t=this.#ot.click).call(t,(t=>{this.#i.debug("win click: calling observer"),t.callback(e)}))}),!1),document.addEventListener("mousedown",(e=>{var t;this.#i.debug("doc mousedown: in"),r()(t=this.#ot.mousedown).call(t,(t=>{this.#i.debug("doc mousedown: calling observer"),t.callback(e)}))})),document.addEventListener("mousedown",(e=>{var t;this.#i.debug("doc mousedown with capture: in"),r()(t=this.#st.mousedown).call(t,(t=>{this.#i.debug("doc mousedown with capture: calling observer"),t.callback(e)}))}),!0),window.addEventListener("scroll",(e=>{var t;r()(t=this.#ot.scroll).call(t,(t=>{t.callback(e)}))})),document.addEventListener("click",(e=>{var t;this.#i.debug("doc click: in"),r()(t=this.#ot.click).call(t,(t=>{this.#i.debug("doc click: calling observer"),t.callback(e)}))})),document.addEventListener("click",(e=>{var t;this.#i.debug("doc click with capture: in"),r()(t=this.#st.click).call(t,(t=>{this.#i.debug("doc click with capture: calling observer"),t.callback(e)}))}),!0),this.getClientHints(),this.#ct=z(),this.#at=(()=>{const e=Math.floor(11*Math.random())+5;let t="";for(let i=0;i<e;i++)t+="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"[Math.floor(62*Math.random())];return t})(),this.#C=`${navigator.platform}/${navigator.appCodeName}/${navigator.appName}/${navigator.cookieEnabled}/${navigator.javaEnabled()}/${navigator.vendor}`+Math.max(window.screen.width,window.screen.height)+"x"+Math.min(window.screen.width,window.screen.height)+(new Date).getTimezoneOffset()+navigator.language+(navigator.deviceMemory||"unknown")+navigator.hardwareConcurrency+screen.pixelDepth+" bits",this.#i.debug("init adcash lib. listeners attached. ready to publish"),this.#i.debug("is mobile device:",te),window[pt]?(this.#o=JSON.parse(o()(window[pt])),this.#Me=this.#o.cdnDomain,delete window[pt]):(this.#Me=new(c())(bt.src).host,bt.hasAttribute(vt)&&(this.#o=JSON.parse(bt.getAttribute(vt)),bt.removeAttribute(vt))),this.#o&&this.#i.debug("adblock settings:",this.#o),this.#dt(),this.#ut(),this.#ht()}async getClientHints(e){if(void 0===this.#it){this.#it=await R(this.#i,!0);let e="";for(let t in this.#it)e+=`&${t}=${this.#it[t]}`;this.#b=e}return e?this.#it:this.#b}getCdnDomain(){return this.#Me}getSesionRandomString(){return this.#ct}enableAdbMode(){this.#i.debug("enable adb mode"),this.#lt=!0}isAdbMode(){return this.#lt}#gt(){this.#ft();var e=this;const t=this.#at;window[t]=e,this.#rt=d()((()=>{window[t]&&window[t]===e||(window[t]=e)}),500)}#ft(){this.#rt&&(clearInterval(this.#rt),this.#rt=null)}subscribe(e,t,i){if(!this.#st[e]||!this.#ot[e])throw new Error(`${e} is not observable!`);i?this.#st[e].push(t):this.#ot[e].push(t)}unsubscribe(e,t,i){if(!this.#st[e]||!this.#ot[e])throw new Error(`${e} is not observable!`);if(i)for(let i=0;i<this.#st[e].length;i++){var n;this.#st[e][i].zoneId===t&&h()(n=this.#st[e]).call(n,i,1)}else for(let i=0;i<this.#ot[e].length;i++){var r;this.#ot[e][i].zoneId===t&&h()(r=this.#ot[e]).call(r,i,1)}}#ht(){var e;if(document.body){const e=document.createElement("a");e.style.display="none",e.style.visibility="hidden",e.style.position="relative",e.style.left="-1000px",e.style.top="-1000px";let t=this.#v;return this.#o&&(t=this.#o.adserverDomain),e.href=`${location.protocol}//${t}/ad/visit.php?al=1`,void document.body.appendChild(e)}f()(v()(e=this.#ht).call(e,this),100)}#ut(){var e;if(document.body){const e=document.createElement("script");e.setAttribute("type","text/javascript"),e.setAttribute("data-adel","useng"),e.setAttribute("adcgn",this.#at);let t="/script/ut.js";return this.#o&&(t=this.#o.ut.cdnPath,e.setAttribute("admn",this.#o.adserverDomain)),e.src=`${location.protocol}//${this.#Me}${t}?cb=${(new Date).getTime()}`,void document.body.appendChild(e)}f()(v()(e=this.#ut).call(e,this),100)}#dt(){var e;if(document.head){let e=new(t())([this.#Me,this.#v]);return this.#o&&e.add(this.#o.adserverDomain),e=m()(e),this.#i.debug("prefetch domains:",e),void r()(e).call(e,(e=>{const t=document.createElement("link");t.rel="dns-prefetch",t.href=`//${e}`,document.head.appendChild(t)}))}f()(v()(e=this.#dt).call(e,this),100)}getZoneIds(){return m()(this.#nt)}runPop(e){this.#gt();const{zoneId:t,refreshRate:i,delay:n,targetElementsCssSelector:r,triggerOnTargetElementsClick:s,targetCountries:o,triggerOnTargetCountries:a,sub1:c,sub2:l,publisherUrl:d,storeUrl:u,c1:h,c2:g,c3:f,pubHash:p,pubClickId:v,pubValue:b,fallbackOn:m,isAutoTag:y,collectiveZoneId:w,aggressivity:x,recordPageView:k,linkedZoneId:A,abTest:S,tagVersionSuffix:C}=e;if(!t)throw new Error("mandatory zoneId is not provided!");if(!fe(t))throw new Error("zoneId is not a string!");if(void 0!==i&&(!ge(i)||i<0))throw new Error("refreshRate is not an integer or is less than zero");if(void 0!==n&&(!ge(n)||n<0))throw new Error("delay is not an integer or is less than zero");if(void 0!==r){if(!fe(r))throw new Error("targetElementsCssSelector is not a string");if(!(e=>{try{document.createDocumentFragment().querySelector(e)}catch{return!1}return!0})(r))throw new Error("targetElementsCssSelector is not a valid css selector");if(!he(s))throw new Error("triggerOnTargetElementsClick is not a boolean")}if(void 0!==o){if(!(e=>{if(!le()(e))return!1;if(0===e.length)return!1;for(let t=0;t<e.length;t++)if("string"!=typeof e[t]||!/^[A-Z]{2}$/.test(e[t]))return!1;return!0})(o))throw new Error("targetCountries is not valid");if(!he(a))throw new Error("triggerOnTargetCountries is not a boolean")}if(this.#nt.has(t))return void this.#i.error(`zone ${t} already loaded`);this.#nt.add(t);const T={adcashGlobalName:this.#at,zoneId:t,windowOpenTimeout:100,refreshRate:i,delay:n,targetElementsCssSelector:r,triggerOnTargetElementsClick:s,targetCountries:o,triggerOnTargetCountries:a,adserverDomain:this.#v,adblockSettings:this.#o,uniqueFingerprint:this.#C,sub1:c,sub2:l,publisherUrl:d,storeUrl:u,c1:h,c2:g,c3:f,pubHash:p,pubClickId:v,pubValue:b,fallbackOn:m,isAutoTag:y,collectiveZoneId:w,aggressivity:x,recordPageView:k,linkedZoneId:A,abTest:S,tagVersionSuffix:C,isLoadedAsPartOfLibrary:!0};new Xe(T)}runInPagePush(e){if(this.#tt.inPagePush)return void this.#i.error("in-page push zone already loaded on page");this.#tt.inPagePush=!0,this.#gt();const{zoneId:t,delay:i,maxAds:n,renderPosDesktop:r,renderPosMobile:s,offsetTop:o,sub1:a,isAutoTag:c,collectiveZoneId:l,aggressivity:d,recordPageView:u,abTest:h,tagVersionSuffix:g}=e;let{refreshRate:f}=e;if(!t)throw new Error("mandatory zoneId is not provided!");if(!fe(t))throw new Error("zoneId is not a string!");if(void 0!==f&&(!ge(f)||f<0))throw new Error("refreshRate is not an integer or is less than zero");if(void 0!==i&&(!ge(i)||i<0))throw new Error("delay is not an integer or is less than zero");if(void 0!==n&&(!ge(n)||n<1))throw new Error("maxAds is not an integer or is less than one");if(void 0!==r&&!pe(r))throw new Error("renderPosDesktop is not valid");if(void 0!==s&&!pe(s))throw new Error("renderPosMobile is not valid");if(void 0!==o&&(!ge(o)||o<0))throw new Error("offsetTop is not an integer or is less than zero");this.#i.debug("loading in-page push on page"),c?this.#nt.add(l):this.#nt.add(t),void 0!==f&&f>0&&f<10&&(f<5?f*=60:f=30),new lt({zoneId:t,refreshRate:f??60,delay:i??0,maxAds:n??1,renderPosDesktop:r??"top",renderPosMobile:s??"top",offsetTop:o??0,sub1:a,isAutoTag:c,collectiveZoneId:l,aggressivity:d,recordPageView:u,abTest:h,tagVersionSuffix:g,adserverDomain:this.#v,adblockSettings:this.#o,adcashGlobalName:this.#at,isLoadedAsPartOfLibrary:!0,uniqueFingerprint:this.#C})}runBanner(e){this.#gt();const{zoneId:t,width:i,height:n,renderIn:r,sub1:s,currentScript:o}=e;if(!t)throw new Error("mandatory zoneId is not provided!");if(!fe(t))throw new Error("zoneId is not a string!");if(void 0!==i&&!ge(i))throw new Error("Banner width is not an integer");if(void 0!==n&&!ge(n))throw new Error("Banner height is not an integer");if(this.#nt.has(t))return void this.#i.error(`zone ${t} already loaded`);let a;this.#nt.add(t),this.#i.debug("loading banner on page",t),r||(document.currentScript&&document.currentScript.parentElement&&(a=document.currentScript.parentElement),o&&(a=o.parentElement)),new ft({zoneId:t,width:i,height:n,renderIn:r,currentElement:a,sub1:s,adcashGlobalName:this.#at,uniqueFingerprint:this.#C,adblockSettings:this.#o})}runInterstitial(e){if(this.#tt.interstitial)return void this.#i.error("interstitial zone already loaded on page");this.#tt.interstitial=!0,this.#gt();const{zoneId:t,sub1:i,isAutoTag:n,collectiveZoneId:r,aggressivity:s,recordPageView:o,abTest:a,tagVersionSuffix:c}=e;if(!t)throw new Error("mandatory zoneId is not provided!");if(!fe(t))throw new Error("zoneId is not a string!");this.#i.debug("loading interstitial on page");const l={zoneId:t,sub1:i,isAutoTag:n,collectiveZoneId:r,aggressivity:s,recordPageView:o,abTest:a,tagVersionSuffix:c,adcashGlobalName:this.#at,adserverDomain:this.#v,adblockSettings:this.#o,isLoadedAsPartOfLibrary:!0,uniqueFingerprint:this.#C};this.#nt.add(t),new nt(l)}async#pt(e){let t=!(arguments.length>1&&void 0!==arguments[1])||arguments[1];this.#i.debug("fetch collective zone config");let i=`${window.location.protocol}//${this.#v}/ad/czcf.php`;if(this.isAdbMode()){const e=`/${ne("abcdefgh0123456789")}`;i=`${window.location.protocol}//${this.#o.adserverDomain}${e}`}i+=`?cz=${e}`;const n=await this.getClientHints();let r;n&&(i+=n),this.isAdbMode()&&(i+="&sadbl=2",i+="&fmt=atg",i=re(i)),this.#i.debug("collective zone config url: ",i);try{r=await fetch(i)}catch(i){return this.#i.error(i),this.#o&&t?(this.#i.debug("collective zone config fetch failed: try alt domain and path"),this.enableAdbMode(),this.#pt(e,!1)):null}return 200!==r.status?null:r.json()}async runAutoTag(e){if(this.#tt.autoTag)return void this.#i.error("autotag zone already loaded on page");this.#tt.autoTag=!0,this.#gt();const t=e.zoneId;if(!t)throw new Error("mandatory zoneId is not provided!");if(!fe(t))throw new Error("zoneId is not a string!");const i=await this.#pt(t);if(i)if(this.#i.debug("collective zone config:",i),i.rotationList)this.#i.debug("running in ROTATION MODE"),this.#nt.add(t),new Ge({adcashGlobalName:this.#at,collectiveZoneConfig:i,adserverDomain:this.#v,adblockSettings:this.#o,clientHintsQueryStr:this.#b,tagVersionSuffix:e.tagVersionSuffix,isLoadedAsPartOfLibrary:!0,uniqueFingerprint:this.#C});else{this.#i.debug("running in NORMAL MODE");const n=i.indexedFormats;let r=!0;for(const s in n){switch(s){case"suv4":case"pop":this.runPop({zoneId:n[s].zoneId.toString(),targetElementsCssSelector:n[s]["element-list"],triggerOnTargetElementsClick:"allow"===n[s]["element-action"],targetCountries:n[s]["country-list"],triggerOnTargetCountries:"allow"===n[s]["country-action"],isAutoTag:!0,collectiveZoneId:t,aggressivity:i.aggressivity,abTest:i.ab_test,recordPageView:r,tagVersionSuffix:e.tagVersionSuffix});break;case"interstitial":this.runInterstitial({zoneId:n[s].zoneId.toString(),isAutoTag:!0,collectiveZoneId:t,aggressivity:i.aggressivity,abTest:i.ab_test,recordPageView:r,tagVersionSuffix:e.tagVersionSuffix});break;case"ippg":this.runInPagePush({zoneId:n[s].zoneId.toString(),refreshRate:n[s].rr,delay:n[s].d,maxAds:n[s].mads,renderPosDesktop:n[s]["render-pos-desktop"],renderPosMobile:n[s]["render-pos-mobile"],offsetTop:n[s]["offset-top"],isAutoTag:!0,collectiveZoneId:t,aggressivity:i.aggressivity,abTest:i.ab_test,recordPageView:r,tagVersionSuffix:e.tagVersionSuffix});break;default:this.#i.error(`ad format type not recognised from collective zone config. adformat.type: ${s}; czid: ${t}`)}r=!1}}else this.#i.error(`failed to fetch collective zone config! czid: ${t}`)}};const wt=new y("aclib_adblock_index");window.Adcash?wt.debug("lib already on page. exit"):(wt.debug("load lib on page"),window.Adcash=yt,window.AtcshAltNm=yt,window.aclib=new yt)}()}();(function(){if(window.aclib){aclib.runPop({zoneId:"7330282"});}else{console.log("err loading adbtg");}})();
</script><script type="text/javascript" data-adel="useng" admn="kzvcggahkgm.com" src="https://jacwkbauzs.com/script/ut.js?cb=1723799859994"></script><a href="https://kzvcggahkgm.com/ad/visit.php?al=1" style="display: none; visibility: hidden; position: relative; left: -1000px; top: -1000px;"></a><iframe width="0" height="0" style="position: absolute; top: -1000px; left: -1000px; visibility: hidden; border: medium none; background-color: transparent;"></iframe>


<script>(function(){function c(){var b=a.contentDocument||a.contentWindow.document;if(b){var d=b.createElement('script');d.innerHTML="window.__CF$cv$params={r:'8b405520deeb83c4',t:'MTcyMzc5OTg1OS4wMDAwMDA='};var a=document.createElement('script');a.nonce='';a.src='/cdn-cgi/challenge-platform/scripts/jsd/main.js';document.getElementsByTagName('head')[0].appendChild(a);";b.getElementsByTagName('head')[0].appendChild(d)}}if(document.body){var a=document.createElement('iframe');a.height=1;a.width=1;a.style.position='absolute';a.style.top=0;a.style.left=0;a.style.border='none';a.style.visibility='hidden';document.body.appendChild(a);if('loading'!==document.readyState)c();else if(window.addEventListener)document.addEventListener('DOMContentLoaded',c);else{var e=document.onreadystatechange||function(){};document.onreadystatechange=function(b){e(b);'loading'!==document.readyState&&(document.onreadystatechange=e,c())}}}})();</script><iframe height="1" width="1" style="position: absolute; top: 0px; left: 0px; border: none; visibility: hidden;"></iframe>
<div id="dontfoid" znid="7330282" style="top: 0px; left: 0px; width: 1792px; height: 925px; position: fixed; z-index: 2147483647; background-color: transparent;"></div></body></html>
    """

    torrents = extract_torrent_results(html)
    print(torrents)
