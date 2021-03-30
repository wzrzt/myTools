# movie detect 
## dy2018 some movie

library(rvest)
url = 'https://www.dy2018.com/i/103159.html'
download_links_xpath = '//*[@id="downlist"]/table/tbody/tr/td/a'

alien_resident_html = read_html(url)

download_links = alien_resident_html %>% 
    html_nodes(xpath = download_links_xpath) %>% 
    html_text()

for (download_link in download_links){
    cat(download_link)
    cat('\n')
}
