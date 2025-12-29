import datetime
import re
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from bs4 import BeautifulSoup, NavigableString, Tag
from .paper import Paper, PaperDatabase, PaperExporter
from tenacity import retry, stop_after_attempt, wait_exponential


support_search_args = ["title","abstract","comment","Journal reference","ACM classification",
                       "MSC classification","Report number","arXiv identifier",
                       "Cross-list category","DOI","ORCID","arXiv author ID",
                       "All fields"]




logging.basicConfig(
    filename="app.log",  # 日志文件路径
    filemode="a",        # 追加模式（默认），改为"w"则每次运行覆盖原有日志
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 日志格式
    level=logging.INFO,  # 只记录INFO及以上级别日志
    encoding="utf-8"     # 解决中文乱码问题
)

class ArxivHelper(object):
  def __init__(self,
               search_args_and=None,
               search_args_or=None,
               search_args_not=None,
               date_from_date=None,
               date_to_date=None,
               date_date_type="submitted_date_first",
               abstracts=True,
               size=50,
               order="-announced_date_first"):
    self.search_args_and=search_args_and
    self.search_args_or=search_args_or
    self.search_args_not=search_args_not
    self.date_from_date=date_from_date
    self.date_to_date=date_to_date
    self.date_date_type=date_date_type
    self.abstracts=abstracts
    self.size=size
    self.order=order
    self.total_global = 0
    self.papers = []

  def get_url(self,start):
    index = 0
    res = "https://arxiv.org/search/advanced?advanced="
    if (self.date_from_date is None) or (self.date_to_date is None):
      today = datetime.now().date()
      yesterday = today - timedelta(days=2)
      self.date_to_date = today.strftime("%Y-%m-%d")
      self.date_from_date = yesterday.strftime("%Y-%m-%d")

    if(self.search_args_and==None and self.search_args_or==None and self.search_args_not==None):
        res = res + f"&terms-{index}-operator=AND&terms-{index}-term=&terms-{index}-field=title"

    if self.search_args_and!=None:
        for key,value in self.search_args_and.items():
            if(key not in support_search_args):
                logging.error(f"{key} not in support_search_args")
                continue
            temp_str = f"&terms-{index}-operator=AND&terms-{index}-term={value}&terms-{index}-field={key}"
            res = res + temp_str
            index = index + 1


    if self.search_args_or!=None:
        for key,value in self.search_args_or.items():
            if(key not in support_search_args):
                logging.error(f"{key} not in support_search_args")
                continue
            temp_str = f"&terms-{index}-operator=OR&terms-{index}-term={value}&terms-{index}-field={key}"
            res = res + temp_str
            index = index + 1

    if self.search_args_not != None:
        for key,value in self.search_args_not.items():
            if(key not in support_search_args):
                logging.error(f"{key} not in support_search_args")
                continue
            temp_str = f"&terms-{index}-operator=NOT&terms-{index}-term={value}&terms-{index}-field={key}"
            res = res + temp_str
            index = index + 1


    res+="&classification-physics_archives=all&classification-include_cross_list=include"
    res+="&date-year="
    res+="&date-filter_by=date_range"
    res+=f"&date-from_date={self.date_from_date}"
    res+=f"&date-to_date={self.date_to_date}"
    res+=f"&date-date_type={self.date_date_type}"
    if(self.abstracts):
        res+="&abstracts=show"
    res+=f"&size={self.size}"
    res+=f"&order={self.order}"
    if(start!=0):
      res+=f"&start={start}"
    logging.info(f"url is :{res} ")
    return res
  
  def parse_search_text(self,tag):
      string = ""
      for child in tag.children:
          if isinstance(child, NavigableString):
              string += re.sub(r"\s+", " ", child)
          elif isinstance(child, Tag):
              if child.name == "span" and "search-hit" in child.get("class"):
                  string += re.sub(r"\s+", " ", child.get_text(strip=False))
              elif child.name == "a" and ".style.display" in child.get("onclick"):
                  pass
              else:
                  import pdb

                  pdb.set_trace()
      return string


  def parse_search_html(self,total_global,content) -> list[Paper]:
      soup = BeautifulSoup(content, "html.parser")
      if total_global == 0:
          total = soup.select("#main-container > div.level.is-marginless > div.level-left > h1")[0].text
          # "Showing 1–50 of 2,542,002 results" or "Sorry, your query returned no results"
          if "Sorry" in total:
              self.total_global = 0
              logging.INFO(f"total is {self.total_global}")
              return []
          total = int(total[total.find("of") + 3: total.find("results")].replace(",", ""))
          self.total_global = total
          logging.info(f"total is {self.total_global}")

      results = soup.find_all("li", {"class": "arxiv-result"})
      for result in results:

          url_tag = result.find("a")
          url = url_tag["href"] if url_tag else "No link"

          title_tag = result.find("p", class_="title")
          title = self.parse_search_text(title_tag) if title_tag else "No title"
          title = title.strip()

          date_tag = result.find("p", class_="is-size-7")
          date = date_tag.get_text(strip=True) if date_tag else "No date"
          if "v1" in date:
              # Submitted9 August, 2024; v1submitted 8 August, 2024; originally announced August 2024.
              # 注意空格会被吞掉，这里我们要找最早的提交日期
              v1 = date.find("v1submitted")
              date = date[v1 + 12: date.find(";", v1)]
          else:
              # Submitted8 August, 2024; originally announced August 2024.
              # 注意空格会被吞掉
              submit_date = date.find("Submitted")
              date = date[submit_date + 9: date.find(";", submit_date)]

          category_tag = result.find_all("span", class_="tag")
          categories = [
              category.get_text(strip=True) for category in category_tag if "tooltip" in category.get("class")
          ]

          authors_tag = result.find("p", class_="authors")
          authors = authors_tag.get_text(strip=True)[len("Authors:"):] if authors_tag else "No authors"

          summary_tag = result.find("span", class_="abstract-full")
          abstract = self.parse_search_text(summary_tag) if summary_tag else "No summary"
          abstract = abstract.strip()

          comments_tag = result.find("p", class_="comments")
          comments = comments_tag.get_text(strip=True)[len("Comments:"):] if comments_tag else "No comments"
          self.papers.append(
              Paper(
                  url=url,
                  title=title,
                  first_submitted_date=datetime.strptime(date, "%d %B, %Y"),
                  categories=categories,
                  authors=authors,
                  abstract=abstract,
                  comments=comments,
              )
          )
  
  
  
  @retry(stop=stop_after_attempt(20), wait=wait_exponential(multiplier=1, min=1, max=15))
  def get_content(self,url):
    try:
        response = requests.get(
            url=url,
            verify=False,  
            timeout=10
        )
        response.raise_for_status()
        self.parse_search_html(self.total_global,response.text)


    except requests.exceptions.RequestException as e:
        logging.info("equests.exceptions.RequestException error")    
        raise

  def dump_all_paper(self):
    for index,paper in enumerate(self.papers):
        logging.info(paper.categories[0])
        print(paper.categories[0])


  def run(self):
    url = self.get_url(0)
    self.get_content(url)
    for index in range(50,self.total_global,50):
      url = self.get_url(index)
      self.get_content(url)   
    self.dump_all_paper()
    return self.papers


helper = ArxivHelper()
helper.run()