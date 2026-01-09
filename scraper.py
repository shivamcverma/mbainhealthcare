from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import re
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

PCOMBA_O_URL="https://www.shiksha.com/business-management-studies/mba-in-healthcare-management-chp"
PCOMBA_S_URL="https://www.shiksha.com/business-management-studies/mba-in-healthcare-management-career-chp"
PCOMBA_ADDMISSION_URL="https://www.shiksha.com/business-management-studies/mba-in-healthcare-management-admission-chp"
PCOMBA_Q_URL = "https://www.shiksha.com/tags/healthcare-hospital-tdp-548954"
PCOMBA_QD_URL="https://www.shiksha.com/tags/healthcare-hospital-tdp-548954?type=discussion"


def create_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

# ---------------- UTILITIES ----------------
def scroll_to_bottom(driver, scroll_times=3, pause=1.5):
    for _ in range(scroll_times):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(pause)




def extract_overview_data(driver):
    driver.get(PCOMBA_O_URL)
    WebDriverWait(driver, 15)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    section = soup.find("section", id="chp_section_overview")

    data = {}
    title = soup.find("div",class_="a54c")
    h1 = title.text.strip()
    data["title"] = h1
    # Updated Date
    updated_div = section.select_one(".f48b div span")
    data["updated_on"] = updated_div.get_text(strip=True) if updated_div else None

    # Author Info
    author_block = section.select_one(".be8c p._7417 a")
    author_role = section.select_one(".be8c p._7417 span.b0fc")
    data["author"] = {
        "name": author_block.get_text(strip=True) if author_block else None,
        "profile_url": author_block["href"] if author_block else None,
        "role": author_role.get_text(strip=True) if author_role else None
    }

    section = soup.find(id="wikkiContents_chp_section_overview_0")
    overview_paras = []
    
    if section:
        for p in section.find_all("p"):
            text = p.get_text(" ", strip=True)
            # Only take paragraphs with more than 50 characters (adjust as needed)
            if text and len(text) > 50:
                overview_paras.append(text)
    
    data["overview"] = overview_paras
        
    # Highlights Table
    highlights = {}
    table = section.find("table")
    if table:
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all(["td", "th"])
            if len(cols) == 2:
                highlights[cols[0].get_text(strip=True)] = cols[1].get_text(" ", strip=True)
    data["highlights"] = highlights

    iframe = section.select_one(".vcmsEmbed iframe")
    
    if iframe:
        data["youtube_video"] = iframe.get("src") or iframe.get("data-src")
    else:
        data["youtube_video"] = None

    # FAQs
    faqs = []
    faq_questions = section.select(".sectional-faqs > div.html-0")
    faq_answers = section.select(".sectional-faqs > div._16f53f")

    for q, a in zip(faq_questions, faq_answers):
        question = q.get_text(" ", strip=True).replace("Q:", "").strip()
        answer = a.get_text(" ", strip=True).replace("A:", "").strip()
        faqs.append({
            "question": question,
            "answer": answer
        })

    data["faqs"] = faqs
    toc = []
    toc_wrapper = soup.find("ul", id="tocWrapper")
    if toc_wrapper:
        for li in toc_wrapper.find_all("li"):
            toc.append({
                "title": li.get_text(" ", strip=True),
            })
    data["table_of_contents"] = toc


    # ==============================
    # ELIGIBILITY SECTION
    # ==============================
    eligibility_section = soup.find("section", id="chp_section_eligibility")
    eligibility_data = {}

    if eligibility_section:

        # Heading
        heading = eligibility_section.find("h2")
        eligibility_data["title"] = heading.get_text(strip=True) if heading else None

        # Main content block
        content_block = eligibility_section.select_one(".wikkiContents")

        # Paragraphs
        paras = []
        if content_block:
            for p in content_block.find_all("p"):
                text = p.get_text(" ", strip=True)
                if text:
                    paras.append(text)
        eligibility_data["description"] = paras

        # Bullet points
        bullets = []
        if content_block:
            for li in content_block.find_all("li"):
                bullets.append(li.get_text(" ", strip=True))
        eligibility_data["criteria_points"] = bullets

        # YouTube Video inside eligibility
        iframe = eligibility_section.find("iframe")
        eligibility_data["youtube_video"] = iframe.get("src") if iframe else None

        # Admission Steps
        admission_steps = []
        for ol in eligibility_section.find_all("ol"):
            for li in ol.find_all("li"):
                admission_steps.append(li.get_text(" ", strip=True))
        eligibility_data["admission_process"] = admission_steps

        # ==============================
        # ELIGIBILITY FAQs
        # ==============================
        faqs = []
        faq_questions = eligibility_section.select(".sectional-faqs > div.html-0")
        faq_answers = eligibility_section.select(".sectional-faqs > div._16f53f")

        for q, a in zip(faq_questions, faq_answers):
            faqs.append({
                "question": q.get_text(" ", strip=True).replace("Q:", "").strip(),
                "answer": a.get_text(" ", strip=True).replace("A:", "").strip()
            })

        eligibility_data["faqs"] = faqs

    data["eligibility_section"] = eligibility_data

    # SYLLABUS & SPECIALIZATION SECTION
    # ==============================
    syllabus_section = soup.find("section", id="chp_section_popularspecialization")
    syllabus_data = {}

    if syllabus_section:

        # Section Title
        title = syllabus_section.find("h2")
        syllabus_data["title"] = title.get_text(strip=True) if title else None

        content_block = syllabus_section.select_one(".wikkiContents")

        # Intro Paragraphs
        intro_paras = []
        if content_block:
            for p in content_block.find_all("p"):
                text = p.get_text(" ", strip=True)
                if text and "Source:" not in text:
                    intro_paras.append(text)
        syllabus_data["description"] = intro_paras

        # ==============================
        # SEMESTER-WISE SYLLABUS TABLE
        # ==============================
        semester_syllabus = {}

        tables = content_block.find_all("table") if content_block else []

        if tables:
            syllabus_table = tables[0]   # ✅ FIRST table only
            current_semester = None

            for row in syllabus_table.find_all("tr"):
                th = row.find("th")
                tds = row.find_all("td")

                # Semester Header
                if th and not tds:
                    current_semester = th.get_text(strip=True)
                    semester_syllabus[current_semester] = []

                # Subjects
                elif current_semester and tds:
                    for td in tds:
                        subject = td.get_text(" ", strip=True)
                        if subject:
                            semester_syllabus[current_semester].append(subject)

        syllabus_data["semester_wise_syllabus"] = semester_syllabus

        # ==============================
        # SYLLABUS YOUTUBE VIDEO
        # ==============================
        iframe = syllabus_section.select_one(".vcmsEmbed iframe")
        syllabus_data["youtube_video"] = iframe.get("src") if iframe else None

        # ==============================
        # MBA SPECIALISATIONS TABLE
        # ==============================
        specialisations = []
        tables = content_block.find_all("table") if content_block else []

        if len(tables) > 1:
            spec_table = tables[1]
            rows = spec_table.find_all("tr")[1:]

            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 3:
                    specialisations.append({
                        "specialisation": cols[0].get_text(" ", strip=True),
                        "average_salary": cols[1].get_text(" ", strip=True),
                        "colleges": cols[2].get_text(" ", strip=True)
                    })

        syllabus_data["specialisations"] = specialisations

        # ==============================
        # POPULAR SPECIALIZATION BOX
        # ==============================
        popular_specs = []
        spec_box = syllabus_section.select_one(".specialization-box")

        if spec_box:
            for li in spec_box.select("ul.specialization-list li"):
                popular_specs.append({
                    "name": li.find("a").get_text(strip=True),
                    "url": li.find("a")["href"],
                    "college_count": li.find("p").get_text(strip=True)
                })

        syllabus_data["popular_specializations"] = popular_specs

        # ==============================
        # SYLLABUS FAQs
        # ==============================
        faqs = []
        faq_questions = syllabus_section.select(".sectional-faqs > div.html-0")
        faq_answers = syllabus_section.select(".sectional-faqs > div._16f53f")

        for q, a in zip(faq_questions, faq_answers):
            faqs.append({
                "question": q.get_text(" ", strip=True).replace("Q:", "").strip(),
                "answer": a.get_text(" ", strip=True).replace("A:", "").strip()
            })

        syllabus_data["faqs"] = faqs

    data["syllabus_section"] = syllabus_data

    # ==============================
    # TYPES OF MBA FINANCE COURSES SECTION
    # ==============================
    types_section = soup.find("section", id="chp_section_topratecourses")
    types_data = {}

    if types_section:

        # Section Title
        title = types_section.find("h2")
        types_data["title"] = title.get_text(strip=True) if title else None

        content_block = types_section.select_one(".wikkiContents")

        # Intro Paragraphs
        intro_paras = []
        if content_block:
            # पहला div जिसमें content है
            first_div = content_block.find("div")
            if first_div:
                for p in first_div.select("p"):
                    text = p.get_text(" ", strip=True)
                    if text and "Note -" not in text and "Also read -" not in text:
                        intro_paras.append(text)
        
        types_data["description"] = intro_paras
        
        # ==============================
        # COURSE MODES TABLE
        # ==============================
        course_modes = []
        table = content_block.find("table") if content_block else None

        if table:
            rows = table.find_all("tr")[1:]  # पहली row header है इसलिए skip करें
            for row in rows:
                cols = row.find_all("td")
                if len(cols) == 2:  # यहाँ 2 columns हैं
                    mode_name = cols[0].get_text(strip=True)
                    
                    # Eligibility points निकालें
                    eligibility_points = []
                    ul = cols[1].find("ul")
                    if ul:
                        for li in ul.find_all("li"):
                            eligibility_points.append(li.get_text(" ", strip=True))
                    else:
                        # अगर ul नहीं है तो सीधे text लें
                        text = cols[1].get_text(" ", strip=True)
                        if text:
                            eligibility_points.append(text)
                    
                    course_modes.append({
                        "mode": mode_name,
                        "eligibility": eligibility_points
                    })

        types_data["course_modes"] = course_modes

        # Note about the information
        note = content_block.find("p", string=lambda t: t and "Note -" in t) if content_block else None
        if note:
            types_data["note"] = note.get_text(strip=True)

        # ==============================
        # POPULAR COURSES BOX
        # ==============================
        popular_courses = []
        popular_box = types_section.select_one(".specialization-box")

        if popular_box:
            for li in popular_box.select("ul.specialization-list li"):
                # Course name and link
                course_link_tag = li.find("a")
                strong_tag = li.find("strong")
                
                # Offered by information
                offered_by_tag = li.find("a", href=lambda x: x and "college" in x or "university" in x)
                
                # Rating and reviews
                rating_div = li.select_one(".rating-block")
                reviews_link = li.select_one("a.view_rvws")
                
                # Rating stars width (percentage)
                full_stars = li.select_one(".full_starts")
                rating_percentage = None
                if full_stars and full_stars.has_attr('style'):
                    style = full_stars['style']
                    if 'width:' in style:
                        rating_percentage = style.split('width:')[1].split('%')[0].strip() + '%'
                
                course_data = {
                    "course_name": strong_tag.get_text(strip=True) if strong_tag else None,
                    "course_url": course_link_tag["href"] if course_link_tag else None,
                    "institute_name": offered_by_tag.get_text(strip=True).replace("Offered By", "").strip() if offered_by_tag else None,
                    "institute_url": offered_by_tag["href"] if offered_by_tag else None,
                    "rating": rating_div.get_text(strip=True) if rating_div else None,
                    "rating_percentage": rating_percentage,
                    "reviews_count": reviews_link.get_text(strip=True).replace('reviews', '').strip() if reviews_link else None,
                    "reviews_url": reviews_link["href"] if reviews_link else None
                }
                popular_courses.append(course_data)

        types_data["popular_courses"] = popular_courses

        # ==============================
        # FAQs
        # ==============================
        faqs = []
        faq_section = types_section.select_one(".c358de")
        
        if faq_section:
            faq_items = faq_section.select(".html-0.c5db62")
            
            for faq_item in faq_items:
                question = faq_item.get_text(" ", strip=True).replace("Q:", "").strip()
                
                # अगला sibling जो answer है
                answer_div = faq_item.find_next_sibling("div", class_="_16f53f")
                answer = ""
                if answer_div:
                    answer_content = answer_div.select_one(".cmsAContent")
                    if answer_content:
                        answer = answer_content.get_text(" ", strip=True).replace("A:", "").strip()
                    else:
                        answer = answer_div.get_text(" ", strip=True).replace("A:", "").strip()
                
                faqs.append({
                    "question": question,
                    "answer": answer
                })

        types_data["faqs"] = faqs

    data["types_of_mba_finance_courses"] = types_data

    # POPULAR COLLEGES SECTION
    # ==============================
    popular_colleges_section = soup.find("section", id="chp_section_popularcolleges")
    popular_colleges_data = {}
    
    if popular_colleges_section:
    
        # Section title
        title = popular_colleges_section.find("h2")
        popular_colleges_data["title"] = title.get_text(strip=True) if title else None
    
        content_block = popular_colleges_section.select_one(".wikkiContents")
    
        # ------------------------------
        # Description Paragraphs
        # ------------------------------
        description = []
        if content_block:
            for p in content_block.select("p"):
                text = p.get_text(" ", strip=True)
                if text and "Source:" not in text:
                    description.append(text)
    
        popular_colleges_data["description"] = description
    
        # ------------------------------
        # Tables (Private + Government)
        # ------------------------------
        tables = content_block.find_all("table") if content_block else []
    
        private_colleges = []
        government_colleges = []
    
        # ✅ First table → Private colleges
        if len(tables) >= 1:
            rows = tables[0].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    link = cols[0].find("a")
                    private_colleges.append({
                        "college_name": cols[0].get_text(" ", strip=True),
                        "college_url": link["href"] if link else None,
                        "total_fees": cols[1].get_text(" ", strip=True)
                    })
    
        # ✅ Second table → Government colleges
        if len(tables) >= 2:
            rows = tables[1].find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    link = cols[0].find("a")
                    government_colleges.append({
                        "college_name": cols[0].get_text(" ", strip=True),
                        "college_url": link["href"] if link else None,
                        "fees": cols[1].get_text(" ", strip=True)
                    })
    
        popular_colleges_data["private_colleges"] = private_colleges
        popular_colleges_data["government_colleges"] = government_colleges
    
        # ------------------------------
        # YouTube Video
        # ------------------------------
        iframe = popular_colleges_section.select_one(".vcmsEmbed iframe")
        popular_colleges_data["youtube_video"] = iframe.get("src") if iframe else None
    
    data["popular_colleges_section"] = popular_colleges_data
    
    # ==============================
    # SALARY & CAREER SECTION
    # ==============================
    salary_section = soup.find("section", id="chp_section_salary")
    salary_data = {}

    if salary_section:

        # ------------------------------
        # Title
        # ------------------------------
        title = salary_section.find("h2")
        salary_data["title"] = title.get_text(strip=True) if title else None

        content_block = salary_section.select_one(".wikkiContents")

        description = []
        
        if content_block:
            # पहला div जिसमें सारा content है
            first_div = content_block.find("div")
            if first_div:
                # सिर्फ पहले few paragraphs (tables से पहले)
                for p in first_div.find_all("p"):
                    text = p.get_text(" ", strip=True)
                    if text and not any(keyword in text for keyword in ["Read More:", "Note:", "Suggested Reading for"]):
                        description.append(text)
                    # अगर table मिल जाए तो stop कर दें
                    if p.find_next_sibling() and p.find_next_sibling().name == "table":
                        break

        salary_data["description"] = description
        
        # ------------------------------
        # Tables
        # ------------------------------
        tables = content_block.find_all("table") if content_block else []

        # ✅ Table 1: Job Profiles & Salary (3 columns हैं)
        job_profiles = []
        if len(tables) >= 1:
            first_table = tables[0]
            # Check header row
            header = first_table.find("tr")
            if header:
                headers = [th.get_text(strip=True) for th in header.find_all("th")]
                # अगर 3 columns हैं तो यह job profiles table है
                if len(headers) >= 3:
                    rows = first_table.find_all("tr")[1:]  # Header skip
                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) >= 3:
                            job_profiles.append({
                                "job_position": cols[0].get_text(" ", strip=True),
                                "description": cols[1].get_text(" ", strip=True),
                                "average_salary": cols[2].get_text(" ", strip=True)
                            })
                    salary_data["job_profiles"] = job_profiles
                else:
                    # यह employment areas table हो सकता है
                    employment_areas = []
                    rows = first_table.find_all("tr")[1:]
                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) >= 2:
                            employment_areas.append({
                                "area": cols[0].get_text(" ", strip=True),
                                "description": cols[1].get_text(" ", strip=True)
                            })
                    salary_data["employment_areas"] = employment_areas

        # ✅ Table 2: Top Recruiters (3x3 grid है)
        top_recruiters = []
        if len(tables) >= 2:
            second_table = tables[1]
            # सभी table cells एक flat list में collect करें
            cells = second_table.find_all("td")
            for cell in cells:
                recruiter_name = cell.get_text(" ", strip=True)
                if recruiter_name:
                    top_recruiters.append(recruiter_name)
        
        salary_data["top_recruiters"] = top_recruiters

        # ✅ Note about salary information
        note_paragraph = None
        if content_block:
            note_paragraph = content_block.find("p", string=lambda t: t and "Note:" in t)
            if not note_paragraph:
                note_paragraph = content_block.find("p", string=lambda t: t and "Note -" in t)
        
        if note_paragraph:
            salary_data["note"] = note_paragraph.get_text(strip=True)
        

        # ------------------------------
        # FAQs
        # ------------------------------
        faqs = []
        
        # Method 1: सीधे सभी FAQ questions निकालें
        faq_questions = salary_section.select(".html-0.c5db62.listener")
        
        for q in faq_questions:
            question = q.get_text(" ", strip=True).replace("Q:", "").strip()

            # Answer container ढूंढें
            answer_div = q.find_next_sibling("div", class_="_16f53f")
            answer = ""
            
            if answer_div:
                answer_content = answer_div.select_one(".cmsAContent")
                if answer_content:
                    # <p> और अन्य tags को सही तरीके से निकालें
                    answer_texts = []
                    for elem in answer_content.find_all(["p", "ol", "li", "table"]):
                        if elem.name == "table":
                            # Table content को special handling की जरूरत है
                            table_text = elem.get_text(" ", strip=True)
                            answer_texts.append(f"Table: {table_text}")
                        else:
                            text = elem.get_text(" ", strip=True)
                            if text:
                                answer_texts.append(text)
                    
                    answer = " ".join(answer_texts) if answer_texts else answer_content.get_text(" ", strip=True)
                else:
                    answer = answer_div.get_text(" ", strip=True)
            
            answer = answer.replace("A:", "").strip()
            
            if question and answer:
                faqs.append({
                    "question": question,
                    "answer": answer
                })

        salary_data["faqs"] = faqs

    data["salary_section"] = salary_data

    study_section = soup.select_one("section#chp_section_studyabroadcourses")

    study_abroad_data = {}

    if study_section:
        # -------- Title --------
        title_tag = study_section.select_one("h2.tbSec2")
        if title_tag:
            study_abroad_data["title"] = title_tag.get_text(strip=True)

        # -------- Description --------
        desc_paragraphs = study_section.select("div#wikkiContents_chp_section_studyabroadcourses_0 > div > p")
        description = " ".join(p.get_text(" ", strip=True) for p in desc_paragraphs if p.get_text(strip=True))
        if description:
            study_abroad_data["description"] = description

        # -------- University Table --------
        table = study_section.select_one("div#wikkiContents_chp_section_studyabroadcourses_0 table")
        universities = []
        if table:
            rows = table.find_all("tr")
            headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) == len(headers):
                    uni_data = {
                        headers[i]: cols[i].get_text(" ", strip=True) for i in range(len(headers))
                    }
                    # Also capture the link if available
                    link_tag = cols[0].find("a")
                    if link_tag and link_tag.get("href"):
                        uni_data["link"] = link_tag["href"]
                    universities.append(uni_data)
        if universities:
            study_abroad_data["universities"] = universities

    # Add to main data
    if study_abroad_data:
        data["study_abroad_courses"] = study_abroad_data
    # FAQ SECTION
    # ==============================
    faq_section = soup.find("section", id="chp_section_faqs")
    faq_data = {}

    if faq_section:

        # ------------------------------
        # Title
        # ------------------------------
        title = faq_section.find("h2")
        faq_data["title"] = title.get_text(strip=True) if title else None

        content_block = faq_section.select_one(".wikkiContents")
        
        # ------------------------------
        # Introduction
        # ------------------------------
        description = []
        if content_block:
            first_div = content_block.find("div")
            if first_div:
                for p in first_div.find_all("p"):
                    text = p.get_text(" ", strip=True)
                    if text:
                        description.append(text)
        
        faq_data["introduction"] = description
        
        # ------------------------------
        # FAQ Questions & Answers
        # ------------------------------
        faqs = []
        
        # सभी FAQ questions निकालें
        faq_questions = faq_section.select(".html-0.c5db62.listener")
        
        for question_div in faq_questions:
            question_text = question_div.get_text(" ", strip=True).replace("Q:", "").strip()

            # Answer container ढूंढें
            answer_div = question_div.find_next_sibling("div", class_="_16f53f")
            answer_text = ""
            
            if answer_div:
                answer_content = answer_div.select_one(".cmsAContent")
                if answer_content:
                    # पूरे answer को structured तरीके से निकालें
                    answer_parts = []
                    
                    # Paragraphs
                    for p in answer_content.find_all("p"):
                        text = p.get_text(" ", strip=True)
                        if text:
                            answer_parts.append(text)
                    
                    # Lists (ul/ol)
                    for list_elem in answer_content.find_all(["ul", "ol"]):
                        list_items = []
                        for li in list_elem.find_all("li"):
                            item_text = li.get_text(" ", strip=True)
                            if item_text:
                                list_items.append(item_text)
                        if list_items:
                            answer_parts.append("List: " + "; ".join(list_items))
                    
                    # Tables
                    for table in answer_content.find_all("table"):
                        # Table की basic information
                        table_data = []
                        rows = table.find_all("tr")
                        for row in rows:
                            cells = row.find_all(["th", "td"])
                            row_data = [cell.get_text(" ", strip=True) for cell in cells if cell.get_text(strip=True)]
                            if row_data:
                                table_data.append(" | ".join(row_data))
                        
                        if table_data:
                            answer_parts.append("Table: " + " || ".join(table_data))
                    
                    # अगर कोई direct text है (lists, tables के बिना)
                    if not answer_parts:
                        answer_text = answer_content.get_text(" ", strip=True)
                    else:
                        answer_text = " ".join(answer_parts)
                    
                    # "A:" remove करें अगर है तो
                    answer_text = answer_text.replace("A:", "").strip()
                else:
                    # अगर .cmsAContent नहीं है तो सीधे text लें
                    answer_text = answer_div.get_text(" ", strip=True).replace("A:", "").strip()
            
            if question_text and answer_text:
                faq = {
                    "question": question_text,
                    "answer": answer_text
                }
                
                # अगर answer में table data है तो उसे अलग से भी store करें
                if answer_content:
                    tables_in_answer = answer_content.find_all("table")
                    if tables_in_answer:
                        faq["has_table"] = True
                        
                        # पहले table की detailed data (अगर जरूरी हो)
                        table_data = []
                        for idx, table in enumerate(tables_in_answer):
                            table_rows = []
                            rows = table.find_all("tr")
                            for row in rows:
                                cells = row.find_all(["th", "td"])
                                row_data = []
                                for cell in cells:
                                    cell_text = cell.get_text(strip=True)
                                    
                                    # Check for links in cells
                                    links = cell.find_all("a")
                                    link_data = []
                                    for link in links:
                                        link_text = link.get_text(strip=True)
                                        link_href = link.get("href", "")
                                        if link_text:
                                            link_data.append({
                                                "text": link_text,
                                                "url": link_href
                                            })
                                    
                                    row_data.append({
                                        "text": cell_text,
                                        "links": link_data if link_data else None
                                    })
                                table_rows.append(row_data)
                            
                            if table_rows:
                                table_data.append({
                                    "table_index": idx,
                                    "rows": table_rows
                                })
                        
                        if table_data:
                            faq["table_data"] = table_data
                
                faqs.append(faq)
        
        faq_data["faqs"] = faqs
        
        # ------------------------------
        # Total FAQs Count
        # ------------------------------
        faq_data["total_faqs"] = len(faqs)

    data["faq_section"] = faq_data

    return data

# def scrape_syllabus_section(driver):
#     driver.get(PCOMBA_C_URL)
#     time.sleep(3)
#     soup = BeautifulSoup(driver.page_source, "html.parser")
  
#     syllabus_data = {}
    
#     syllabus_section = soup.find("section", id="chp_syllabus_overview")
    
#     if not syllabus_section:
#         return syllabus_data
    
#     title = soup.find("div", class_="a54c")
#     h1 = title.text.strip() if title else None
#     syllabus_data["title"] = h1
    
#     # Updated Date
#     updated_div = syllabus_section.select_one(".f48b div span")
#     syllabus_data["updated_on"] = updated_div.get_text(strip=True) if updated_div else None

#     # Author Info
#     author_block = syllabus_section.select_one(".be8c p._7417 a")
#     author_role = syllabus_section.select_one(".be8c p._7417 span.b0fc")
#     syllabus_data["author"] = {
#         "name": author_block.get_text(strip=True) if author_block else None,
#         "profile_url": author_block["href"] if author_block else None,
#         "role": author_role.get_text(strip=True) if author_role else None
#     }
    
#     # ------------------------------
#     # CONTENT BLOCK
#     # ------------------------------
#     content_block = syllabus_section.select_one(".wikkiContents")
    
#     if content_block:
#         main_content = content_block.find("div")
        
#         if main_content:
#             # ------------------------------
#             # INTRODUCTION PARAGRAPHS
#             # ------------------------------
#             intro_paragraphs = []
            
#             for elem in main_content.find_all(["p", "h2", "h3"]):
#                 if elem.find("table"):
#                     break
                
#                 if elem.name == "p":
#                     text = elem.get_text(" ", strip=True)
#                     if text and len(text) > 20:
#                         unwanted_keywords = [
#                             "Read More:", "Also Read:", "DFP-Banner", 
#                             "Note:", "Note -", "Source:", "Download"
#                         ]
#                         if not any(keyword in text for keyword in unwanted_keywords):
#                             intro_paragraphs.append(text)
                
#                 elif elem.name == "h2" and "Syllabus" in elem.get_text():
#                     break
            
#             syllabus_data["introduction"] = intro_paragraphs
            
#             # ------------------------------
#             # ALL TABLES EXTRACTION
#             # ------------------------------
#             all_tables = main_content.find_all("table")
            
#             # Table 1: Semester-wise Subjects
#             semester_subjects = {}
#             if len(all_tables) >= 1:
#                 table1 = all_tables[0]
#                 current_semester = None
                
#                 rows = table1.find_all("tr")
#                 for row in rows:
#                     th = row.find("th")
#                     if th:
#                         header_text = th.get_text(strip=True)
#                         if "Semester 1" in header_text:
#                             current_semester = "semester_1"
#                             semester_subjects[current_semester] = []
#                         elif "Semester 2" in header_text:
#                             current_semester = "semester_2"
#                             semester_subjects[current_semester] = []
#                         elif "Semester 3" in header_text:
#                             current_semester = "semester_3"
#                             semester_subjects[current_semester] = []
#                         elif "Semester 4" in header_text:
#                             current_semester = "semester_4"
#                             semester_subjects[current_semester] = []
                    
#                     elif current_semester and row.find("td"):
#                         cols = row.find_all("td")
#                         if len(cols) >= 2:
#                             subject1 = cols[0].get_text(strip=True)
#                             subject2 = cols[1].get_text(strip=True)
                            
#                             if subject1 and subject1 not in ["-", ""]:
#                                 semester_subjects[current_semester].append(subject1)
#                             if subject2 and subject2 not in ["-", ""]:
#                                 semester_subjects[current_semester].append(subject2)
            
#             syllabus_data["semester_subjects"] = semester_subjects
            
#             # Table 2: Core Subjects
#             core_subjects = []
#             for table in all_tables:
#                 first_row = table.find("tr")
#                 if first_row:
#                     th_text = first_row.get_text(strip=True)
#                     if "Subject Title" in th_text and "Subject Details" in th_text:
#                         prev_elem = table.find_previous("p")
#                         if prev_elem and "core" in prev_elem.get_text().lower():
#                             rows = table.find_all("tr")[1:]
#                             for row in rows:
#                                 cols = row.find_all("td")
#                                 if len(cols) >= 2:
#                                     subject_title = cols[0].get_text(strip=True)
#                                     subject_details = cols[1].get_text(strip=True)
#                                     if subject_title and subject_details:
#                                         core_subjects.append({
#                                             "subject_title": subject_title,
#                                             "subject_details": subject_details
#                                         })
#                             break
            
#             syllabus_data["core_subjects"] = core_subjects
            
#             # Table 3: Elective Subjects
#             elective_subjects = []
#             for table in all_tables:
#                 first_row = table.find("tr")
#                 if first_row:
#                     th_text = first_row.get_text(strip=True)
#                     if "Subject Title" in th_text and "Subject Details" in th_text:
#                         prev_elem = table.find_previous("p")
#                         if prev_elem and "elective" in prev_elem.get_text().lower():
#                             rows = table.find_all("tr")[1:]
#                             for row in rows:
#                                 cols = row.find_all("td")
#                                 if len(cols) >= 2:
#                                     subject_title = cols[0].get_text(strip=True)
#                                     subject_details = cols[1].get_text(strip=True)
#                                     if subject_title and subject_details:
#                                         elective_subjects.append({
#                                             "subject_title": subject_title,
#                                             "subject_details": subject_details
#                                         })
#                             break
            
#             syllabus_data["elective_subjects"] = elective_subjects
            
#             # Table 4: Detailed Semester Syllabus
#             detailed_syllabus = []
#             for table in all_tables:
#                 first_row = table.find("tr")
#                 if first_row:
#                     cols = first_row.find_all(["th", "td"])
#                     if len(cols) >= 3 and "Semester" in cols[0].get_text():
#                         rows = table.find_all("tr")[1:]
#                         for row in rows:
#                             row_cols = row.find_all(["td", "th"])
#                             if len(row_cols) >= 3:
#                                 semester_num = row_cols[0].get_text(strip=True)
#                                 core_elective = row_cols[1].get_text(strip=True)
                                
#                                 subjects_list = []
#                                 ol = row_cols[2].find("ol")
#                                 if ol:
#                                     for li in ol.find_all("li"):
#                                         subject = li.get_text(strip=True)
#                                         if subject:
#                                             subjects_list.append(subject)
#                                 else:
#                                     text = row_cols[2].get_text("\n", strip=True)
#                                     lines = [line.strip() for line in text.split("\n") if line.strip()]
#                                     for line in lines:
#                                         if re.match(r'^\d+[\.\)]', line):
#                                             line = re.sub(r'^\d+[\.\)]\s*', '', line)
#                                         if line:
#                                             subjects_list.append(line)
                                
#                                 if semester_num and subjects_list:
#                                     detailed_syllabus.append({
#                                         "semester": semester_num,
#                                         "type": core_elective,
#                                         "subjects": subjects_list
#                                     })
#                         break
            
#             syllabus_data["detailed_syllabus"] = detailed_syllabus
            
#             # ------------------------------
#             # RECOMMENDED BOOKS WITH HEADING
#             # ------------------------------
#             recommended_books = []
#             books_intro = None
            
#             for table in all_tables:
#                 if "Book title" in table.get_text():
#                     prev_elem = table.find_previous("p")
#                     if prev_elem:
#                         books_intro = prev_elem.get_text(strip=True)
                    
#                     rows = table.find_all("tr")[1:]
#                     for row in rows:
#                         cols = row.find_all("td")
#                         if len(cols) >= 3:
#                             book_title = cols[0].get_text(strip=True)
#                             author = cols[1].get_text(strip=True)
#                             description = cols[2].get_text(strip=True)
                            
#                             if book_title and author:
#                                 recommended_books.append({
#                                     "book_title": book_title,
#                                     "author": author,
#                                     "description": description
#                                 })
#                     break
            
#             syllabus_data["recommended_books"] = {
#                 "introduction": books_intro,
#                 "books": recommended_books
#             }
            
#             # ------------------------------
#             # PDF LINKS EXTRACTION WITH JAVASCRIPT
#             # ------------------------------
#             # Method 1: JavaScript execute करके actual URLs निकालें
#             def extract_pdf_links_with_js():
#                 """JavaScript execution के through PDF links निकालें"""
#                 try:
#                     # JavaScript code जो Shiksha website पर PDF links decode करता है
#                     js_code = """
#                     // Shiksha के PDF decoding logic का simulation
#                     function decodeShikshaPDFLink(encrypted) {
#                         // ये एक sample function है, actual logic website के JavaScript में है
#                         // आपको Shiksha के actual JavaScript को analyze करना होगा
#                         try {
#                             // Common pattern: base64 decode
#                             return atob(encrypted);
#                         } catch(e) {
#                             return encrypted;
#                         }
#                     }
                    
#                     // सभी PDF links collect करें
#                     var pdfLinks = [];
#                     var pdfAnchors = document.querySelectorAll('a[data-link]');
                    
#                     pdfAnchors.forEach(function(anchor) {
#                         var dataLink = anchor.getAttribute('data-link');
#                         var decodedUrl = decodeShikshaPDFLink(dataLink);
#                         pdfLinks.push({
#                             'text': anchor.textContent.trim(),
#                             'data_link': dataLink,
#                             'decoded_url': decodedUrl
#                         });
#                     });
                    
#                     return JSON.stringify(pdfLinks);
#                     """
                    
#                     pdf_links_json = driver.execute_script(js_code)
#                     pdf_links = json.loads(pdf_links_json)
#                     return pdf_links
#                 except Exception as e:
#                     print(f"JavaScript execution error: {e}")
#                     return []
            
#             # PDF links extract करें
#             pdf_links_data = extract_pdf_links_with_js()
            
#             # ------------------------------
#             # TOP COLLEGES WITH SYLLABUS PDFs
#             # ------------------------------
#             top_colleges = []
#             for table in all_tables:
#                 if "MBA in Finance Colleges in India" in table.get_text():
#                     rows = table.find_all("tr")[1:]
#                     for row in rows:
#                         cols = row.find_all("td")
#                         if len(cols) >= 2:
#                             college_name = cols[0].get_text(strip=True)
                            
#                             pdf_link = cols[1].find("a")
#                             pdf_url = None
                            
#                             if pdf_link:
#                                 data_link = pdf_link.get("data-link", "")
                                
#                                 # JavaScript से decoded URL ढूंढें
#                                 if pdf_links_data:
#                                     for pdf_data in pdf_links_data:
#                                         if pdf_data['data_link'] == data_link:
#                                             pdf_url = pdf_data.get('decoded_url')
#                                             break
                                
#                                 # अगर decoded नहीं मिला तो data-link store करें
#                                 if not pdf_url:
#                                     pdf_url = data_link
                            
#                             top_colleges.append({
#                                 "college_name": college_name,
                                
#                                 "syllabus_pdf_link": f"https://www.shiksha.com/mba/resources/pdf/{college_name.replace(' ', '-').lower()}-syllabus.pdf" if college_name else None
#                             })
#                     break
            
#             syllabus_data["top_colleges_syllabus"] = top_colleges
            

    
#     return syllabus_data

def scrape_career_overview(driver):
    driver.get(PCOMBA_S_URL)
    soup = BeautifulSoup(driver.page_source,"html.parser")
    section = soup.select_one("section#chp_career_overview")
    if not section:
        return {}

    career_data = {}

    title = soup.find("div", class_="a54c")
    h1 = title.text.strip() if title else None
    career_data ["title"] = h1
    
    # Updated Date
    updated_div = section.select_one(".f48b div span")
    career_data ["updated_on"] = updated_div.get_text(strip=True) if updated_div else None

    # Author Info
    author_block = section.select_one(".be8c p._7417 a")
    author_role = section.select_one(".be8c p._7417 span.b0fc")
    career_data ["author"] = {
        "name": author_block.get_text(strip=True) if author_block else None,
        "profile_url": author_block["href"] if author_block else None,
        "role": author_role.get_text(strip=True) if author_role else None
    }

    content = section.select_one("div#wikkiContents_chp_career_overview_0")
    if not content:
        return career_data

    intro_paras = []

    inner_div = content.find("div", recursive=False)
    if inner_div:
        for p in inner_div.find_all("p", recursive=False):
            text = p.get_text(" ", strip=True)
            if text:
                intro_paras.append(text)

    career_data["overview"] = intro_paras

    # -------------------------
    # All Headings & Content Blocks
    # -------------------------
    sections = []
    current = None

    for tag in content.find_all(["h2", "p", "ul", "table"], recursive=True):
        if tag.name == "h2":
            if current:
                sections.append(current)
            current = {
                "title": tag.get_text(strip=True),
                "content": []
            }

        elif current:

            if tag.name == "table":
                rows = []
                for tr in tag.find_all("tr"):
                    cells = [td.get_text(" ", strip=True) for td in tr.find_all(["th", "td"])]
                    if cells:
                        rows.append(cells)
                if rows:
                    current["content"].append({"value": rows})

    if current:
        sections.append(current)

    career_data["sections"] = sections
    return career_data

def scrape_admission_overview(driver):
    driver.get(PCOMBA_ADDMISSION_URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    data = {
        "title": None,
        "updated_on": None,
        "author": None,
        "overview":"",
        "sections": []
    }

    # ---------------- TITLE ----------------
    title = soup.find("div", class_="a54c")
    data["title"] = title.get_text(strip=True) if title else None

    # ---------------- META SECTION ----------------
    section1 = soup.find(id="chp_admission_overview")
    if section1:
        updated_div = section1.select_one(".f48b div span")
        data["updated_on"] = updated_div.get_text(strip=True) if updated_div else None

        author_block = section1.select_one(".be8c p._7417 a")
        author_role = section1.select_one(".be8c p._7417 span.b0fc")

        data["author"] = {
            "name": author_block.get_text(strip=True) if author_block else None,
            "profile_url": author_block["href"] if author_block else None,
            "role": author_role.get_text(strip=True) if author_role else None
        }

    # ---------------- MAIN CONTENT ----------------
    section = soup.find("div", id="wikkiContents_chp_admission_overview_0")
    if not section:
        return data

    main_container = section.find("div")
    if not main_container:
        return data

    intro_paras = []
    for el in main_container.find_all(["p", "h2", "h3"], recursive=True):
        if el.name in ["h2", "h3"]:
            break  # stop at first heading
        text = el.get_text(" ", strip=True)
        if text:
            intro_paras.append(text)

    data["overview"] = intro_paras
    current_section = None
    for element in main_container.find_all(recursive=True):
        if element.name in ["h2", "h3"]:
            if current_section:
                data["sections"].append(current_section)
            current_section = {"heading": element.get_text(strip=True), "content": []}
        elif element.name == "p" and current_section:
            text = element.get_text(" ", strip=True)
            if text:
                current_section["content"].append({"text": text})
        elif element.name == "ul" and current_section:
            items = [li.get_text(" ", strip=True) for li in element.find_all("li") if li.get_text(strip=True)]
            if items:
                current_section["content"].append({"items": items})
        elif element.name == "table" and current_section:
            rows = [[cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])] for row in element.find_all("tr")]
            if rows:
                current_section["content"].append({"rows": rows})

    if current_section:
        data["sections"].append(current_section)

    return data




def scrape_shiksha_qa(driver):
    driver.get(PCOMBA_Q_URL)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.post-col[questionid][answerid][type='Q']"))
        )
    except:
        print("No Q&A blocks loaded!")
        return {}

    soup = BeautifulSoup(driver.page_source, "html.parser")

    result = {
        "tag_name": None,
        "description": None,
        "stats": {},
        "questions": []
    }

    # Optional: get tag name & description if exists
    tag_head = soup.select_one("div.tag-head")
    if tag_head:
        tag_name_el = tag_head.select_one("h1.tag-p")
        desc_el = tag_head.select_one("p.tag-bind")
        if tag_name_el:
            result["tag_name"] = tag_name_el.get_text(strip=True)
        if desc_el:
            result["description"] = desc_el.get_text(" ", strip=True)

    # Stats
    stats_cells = soup.select("div.ana-table div.ana-cell")
    stats_keys = ["Questions", "Discussions", "Active Users", "Followers"]
    for key, cell in zip(stats_keys, stats_cells):
        count_tag = cell.select_one("b")
        if count_tag:
            value = count_tag.get("valuecount") or count_tag.get_text(strip=True)
            result["stats"][key] = value

    questions_dict = {}

    for post in soup.select("div.post-col[questionid][answerid][type='Q']"):
        q_text_el = post.select_one("div.dtl-qstn .wikkiContents")
        if not q_text_el:
            continue
        question_text = q_text_el.get_text(" ", strip=True)

        # Tags
        tags = [{"tag_name": a.get_text(strip=True), "tag_url": a.get("href")}
                for a in post.select("div.ana-qstn-block .qstn-row a")]

        # Followers
        followers_el = post.select_one("span.followersCountTextArea")
        followers = int(followers_el.get("valuecount", "0")) if followers_el else 0

        # Author
        author_el = post.select_one("div.avatar-col .avatar-name")
        author_name = author_el.get_text(strip=True) if author_el else None
        author_url = author_el.get("href") if author_el else None

        # Answer text
        answer_el = post.select_one("div.avatar-col .rp-txt .wikkiContents")
        answer_text = answer_el.get_text(" ", strip=True) if answer_el else None

        # Upvotes / downvotes
        upvote_el = post.select_one("a.up-thumb.like-a")
        downvote_el = post.select_one("a.up-thumb.like-d")
        upvotes = int(upvote_el.get_text(strip=True)) if upvote_el and upvote_el.get_text(strip=True).isdigit() else 0
        downvotes = int(downvote_el.get_text(strip=True)) if downvote_el and downvote_el.get_text(strip=True).isdigit() else 0

        # Posted time (if available)
        time_el = post.select_one("div.col-head span")
        posted_time = time_el.get_text(strip=True) if time_el else None

        # Group by question
        if question_text not in questions_dict:
            questions_dict[question_text] = {
                "tags": tags,
                "followers": followers,
                "answers": []
            }
        questions_dict[question_text]["answers"].append({
            "author": {"name": author_name, "profile_url": author_url},
            "answer_text": answer_text,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "posted_time": posted_time
        })

    # Convert dict to list
    for q_text, data in questions_dict.items():
        result["questions"].append({
            "question_text": q_text,
            "tags": data["tags"],
            "followers": data["followers"],
            "answers": data["answers"]
        })

    return result


def scrape_tag_cta_D_block(driver):
    driver.get(PCOMBA_QD_URL)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    result = {
        "questions": []  # store all Q&A and discussion blocks
    }

    # Scrape all Q&A and discussion blocks
    qa_blocks = soup.select("div.post-col[questionid][answerid][type='Q'], div.post-col[questionid][answerid][type='D']")
    for block in qa_blocks:
        block_type = block.get("type", "Q")
        qa_data = {
          
            "posted_time": None,
            "tags": [],
            "question_text": None,
            "followers": 0,
            "views": 0,
            "author": {
                "name": None,
                "profile_url": None,
            },
            "answer_text": None,
        }

        # Posted time
        posted_span = block.select_one("div.col-head span")
        if posted_span:
            qa_data["posted_time"] = posted_span.get_text(strip=True)

        # Tags
        tag_links = block.select("div.ana-qstn-block div.qstn-row a")
        for a in tag_links:
            qa_data["tags"].append({
                "tag_name": a.get_text(strip=True),
                "tag_url": a.get("href")
            })

        # Question / Discussion text
        question_div = block.select_one("div.dtl-qstn a div.wikkiContents")
        if question_div:
            qa_data["question_text"] = question_div.get_text(" ", strip=True)

        # Followers
        followers_span = block.select_one("span.followersCountTextArea, span.follower")
        if followers_span:
            qa_data["followers"] = int(followers_span.get("valuecount", "0"))

        # Views
        views_span = block.select_one("div.right-cl span.viewers-span")
        if views_span:
            views_text = views_span.get_text(strip=True).split()[0].replace("k","000").replace("K","000")
            try:
                qa_data["views"] = int(views_text)
            except:
                qa_data["views"] = views_text

        # Author info
        author_name_a = block.select_one("div.avatar-col a.avatar-name")
        if author_name_a:
            qa_data["author"]["name"] = author_name_a.get_text(strip=True)
            qa_data["author"]["profile_url"] = author_name_a.get("href")

        # Answer / Comment text
        answer_div = block.select_one("div.avatar-col div.wikkiContents")
        if answer_div:
            paragraphs = answer_div.find_all("p")
            if paragraphs:
                qa_data["answer_text"] = " ".join(p.get_text(" ", strip=True) for p in paragraphs)
            else:
                # Sometimes discussion/comment text is direct text without <p>
                qa_data["answer_text"] = answer_div.get_text(" ", strip=True)

        result["questions"].append(qa_data)

    return result



def scrape_mba_colleges():
    driver = create_driver()

      

    try:
       data = {
              "mba_in_healthcare_management":{
                "overviews":extract_overview_data(driver),
                # "syllabus":scrape_syllabus_section(driver),
                "career":scrape_career_overview(driver),
                "addmision":scrape_admission_overview(driver),
                "QA":{
                 "QA_ALL":scrape_shiksha_qa(driver),
                 "QA_D":scrape_tag_cta_D_block(driver),
                },
                
                   }
                }
       
       
        
        # data["overview"] =  overviews
        # data["courses"] = courses

    finally:
        driver.quit()
    
    return data



import time

DATA_FILE =  "distance_mba_data.json"
UPDATE_INTERVAL = 6 * 60 * 60  # 6 hours

def auto_update_scraper():
    # Check last modified time
    # if os.path.exists(DATA_FILE):
    #     last_mod = os.path.getmtime(DATA_FILE)
    #     if time.time() - last_mod < UPDATE_INTERVAL:
    #         print("⏱️ Data is recent, no need to scrape")
    #         return

    print("🔄 Scraping started")
    data = scrape_mba_colleges()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("✅ Data scraped & saved successfully")

if __name__ == "__main__":

    auto_update_scraper()

