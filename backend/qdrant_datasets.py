from qdrant_builder import qdrant_builder

datasets = [
[
  {
    "questions": "Who is the dean of the College of Engineering?",
    "command": "select dean from colleges where name = 'College of engineering';",
    "lang": "en"
  },
  {
    "questions": "کێ ڕاگری کۆلێژی ئەندازیارییە؟",
    "command": "select dean from colleges where name = 'College of engineering';",
    "lang": "ku"
  },
  {
    "questions": "What is the email of the College of Engineering?",
    "command": "select college_email from colleges where name = 'College of engineering';",
    "lang": "en"
  },
  {
    "questions": "ئیمەیڵی کۆلێژی ئەندازیاری چییە؟",
    "command": "select college_email from colleges where name = 'College of engineering';",
    "lang": "ku"
  },
  {
    "questions": "Where is the College of Engineering located?",
    "command": "select location from colleges where name = 'College of engineering';",
    "lang": "en"
  },
  {
    "questions": "کۆلێژی ئەندازیاری لە کوێ دایە؟",
    "command": "select location from colleges where name = 'College of engineering';",
    "lang": "ku"
  },
  {
    "questions": "What year was the College of Engineering established?",
    "command": "select establishment_year from colleges where name = 'College of engineering';",
    "lang": "en"
  },
  {
    "questions": "کۆلێژی ئەندازیاری لە کام ساڵ دامەزراوە؟",
    "command": "select establishment_year from colleges where name = 'College of engineering';",
    "lang": "ku"
  },
  {
    "questions": "What is the building number of the College of Engineering?",
    "command": "select building_number from colleges where name = 'College of engineering';",
    "lang": "en"
  },
  {
    "questions": "ژمارەی بنای کۆلێژی ئەندازیاری چییە؟",
    "command": "select building_number from colleges where name = 'College of engineering';",
    "lang": "ku"
  },
  {
    "questions": "Show the website of the College of Engineering.",
    "command": "select website_url from colleges where name = 'College of engineering';",
    "lang": "en"
  },
  {
    "questions": "ماڵپەڕی کۆلێژی ئەندازیاری پیشان بدە.",
    "command": "select website_url from colleges where name = 'College of engineering';",
    "lang": "ku"
  },
  {
    "questions": "Give a description of the College of Engineering.",
    "command": "select description from colleges where name = 'College of engineering';",
    "lang": "en"
  },
  {
    "questions": "وەسفی کۆلێژی ئەندازیاری بدە.",
    "command": "select description from colleges where name = 'College of engineering';",
    "lang": "ku"
  },
  {
    "questions": "List all engineering departments.",
    "command": "select department_name from engineering_departments;",
    "lang": "en"
  },
  {
    "questions": "هەموو بەشەکانی ئەندازیاری پیشان بدە.",
    "command": "select department_name from engineering_departments;",
    "lang": "ku"
  },
  {
    "questions": "Who is the head of the Computer Engineering department?",
    "command": "select department_head from engineering_departments where department_name = 'Computer engineering';",
    "lang": "en"
  },
  {
    "questions": "کێ سەرۆکی بەشی ئەندازیاری کۆمپیوتەرە؟",
    "command": "select department_head from engineering_departments where department_name = 'Computer engineering';",
    "lang": "ku"
  },
  {
    "questions": "What is the duration of the Civil Engineering department?",
    "command": "select duration from engineering_departments where department_name = 'Civil Engineering';",
    "lang": "en"
  },
  {
    "questions": "ماوەی خوێندنی بەشی ئەندازیاری ئاوە چەند سەمێسترە؟",
    "command": "select duration from engineering_departments where department_name = 'Civil Engineering';",
    "lang": "ku"
  },
  {
    "questions": "What is the description of the Architecture Engineering department?",
    "command": "select department_description from engineering_departments where department_name = 'Architecture Engineering';",
    "lang": "en"
  },
  {
    "questions": "وەسفی بەشی ئەندازیاری مەعماری چییە؟",
    "command": "select department_description from engineering_departments where department_name = 'Architecture Engineering';",
    "lang": "ku"
  },
  {
    "questions": "Give the head of Water Resources Engineering department.",
    "command": "select department_head from engineering_departments where department_name = 'Water Resources Engineering';",
    "lang": "en"
  },
  {
    "questions": "سەرۆکی بەشی سەرچاوەکانی ئاو کێیە؟",
    "command": "select department_head from engineering_departments where department_name = 'Water Resources Engineering';",
    "lang": "ku"
  },
  {
    "questions": "List all staff members in the Computer Engineering department.",
    "command": "select full_name from staff where department_id = (select department_id from engineering_departments where department_name = 'Computer engineering');",
    "lang": "en"
  },
  {
    "questions": "هەموو کارمەندانی بەشی ئەندازیاری کۆمپیوتەر پێشانی بدە.",
    "command": "select full_name from staff where department_id = (select department_id from engineering_departments where department_name = 'Computer engineering');",
    "lang": "ku"
  },
  {
    "questions": "What is the email of staff member named Ahmad?",
    "command": "select email from staff where full_name = 'Ahmad';",
    "lang": "en"
  },
  {
    "questions": "ئیمەیڵی کارمەندی بە ناوی ئەحمەد چییە؟",
    "command": "select email from staff where full_name = 'Ahmad';",
    "lang": "ku"
  },
  {
    "questions": "What is the title of Dr. Sara?",
    "command": "select title from staff where full_name = 'Dr. Sara';",
    "lang": "en"
  },
  {
    "questions": "ناونیشانی د.سارا چییە؟",
    "command": "select title from staff where full_name = 'Dr. Sara';",
    "lang": "ku"
  },
  {
    "questions": "List all academic years.",
    "command": "select academic_year from academic_years;",
    "lang": "en"
  },
  {
    "questions": "هەموو ساڵی خوێندندا پیشان بدە.",
    "command": "select academic_year from academic_years;",
    "lang": "ku"
  },
  {
    "questions": "What semesters are available for 2023/2024?",
    "command": "select semester_name from semesters where academic_year_id = (select academic_year_id from academic_years where academic_year = '2023/2024');",
    "lang": "en"
  },
  {
    "questions": "کام سەمێستر بۆ ساڵی خوێندنی ٢٠٢٣/٢٠٢٤ بەردەستە؟",
    "command": "select semester_name from semesters where academic_year_id = (select academic_year_id from academic_years where academic_year = '2023/2024');",
    "lang": "ku"
  },
  {
    "questions": "List all lectures in the Computer Engineering department.",
    "command": "select lecture_name from lectures where department_id = (select department_id from engineering_departments where department_name = 'Computer engineering');",
    "lang": "en"
  },
  {
    "questions": "هەموو وانەکانی بەشی ئەندازیاری کۆمپیوتەر پێشانی بدە.",
    "command": "select lecture_name from lectures where department_id = (select department_id from engineering_departments where department_name = 'Computer engineering');",
    "lang": "ku"
  },
  {
    "questions": "Which year is Data Structures taught in?",
    "command": "select academic_year from academic_years where academic_year_id = (select academic_year_id from lectures where lecture_name = 'Data Structures');",
    "lang": "en"
  },
  {
    "questions": "وانەی ڕووکارە داتاکان لە کام ساڵ خوێندراوە؟",
    "command": "select academic_year from academic_years where academic_year_id = (select academic_year_id from lectures where lecture_name = 'Data Structures');",
    "lang": "ku"
  },
  {
    "questions": "When is the final exam for the Computer Networks lecture?",
    "command": "select exam_date, exam_time from final_exam_schedule where lecture_id = (select lecture_id from lectures where lecture_name = 'Computer Networks');",
    "lang": "en"
  },
  {
    "questions": "کات و ڕۆژی تاقیکردنەوەی کۆتایی بۆ وانەی تۆڕە کۆمپیوتەرەکان کامە؟",
    "command": "select exam_date, exam_time from final_exam_schedule where lecture_id = (select lecture_id from lectures where lecture_name = 'Computer Networks');",
    "lang": "ku"
  },
  {
    "questions": "What is the schedule for all final exams in semester 1?",
    "command": "select * from final_exam_schedule where semester_id = (select semester_id from semesters where semester_name = 'Semester 1');",
    "lang": "en"
  },
  {
    "questions": "خشتەی تەواوی تاقیکردنەوەی کۆتایی بۆ سەمێستەری یەکەم پێشانی بدە.",
    "command": "select * from final_exam_schedule where semester_id = (select semester_id from semesters where semester_name = 'Semester 1');",
    "lang": "ku"
  },
  {
    "questions": "Which teacher supervises the Operating Systems exam?",
    "command": "select staff_id from final_exam_schedule where lecture_id = (select lecture_id from lectures where lecture_name = 'Operating Systems');",
    "lang": "en"
  },
  {
    "questions": "کام مامۆستا سەرپەرشتی تاقیکردنەوەی Operating Systems دەکات؟",
    "command": "select staff_id from final_exam_schedule where lecture_id = (select lecture_id from lectures where lecture_name = 'Operating Systems');",
    "lang": "ku"
  },
  {
    "questions": "Where will the Computer Architecture exam be held?",
    "command": "select location_name from exam_locations where location_id = (select location_id from final_exam_schedule where lecture_id = (select lecture_id from lectures where lecture_name = 'Computer Architecture'));",
    "lang": "en"
  },
  {
    "questions": "تاقیکردنەوەی ڕێکخستنی کۆمپیوتەر لە کوێ ئەنجام دەدرێت؟",
    "command": "select location_name from exam_locations where location_id = (select location_id from final_exam_schedule where lecture_id = (select lecture_id from lectures where lecture_name = 'Computer Architecture'));",
    "lang": "ku"
  },
  {
    "questions": "List all exam locations.",
    "command": "select location_name from exam_locations;",
    "lang": "en"
  },
  {
    "questions": "هەموو شوێنەکانی تاقیکردنەوە پێشانی بدە.",
    "command": "select location_name from exam_locations;",
    "lang": "ku"
  },
  {
    "questions": "Which exams are held in Hall A?",
    "command": "select lecture_id from final_exam_schedule where location_id = (select location_id from exam_locations where location_name = 'Hall A');",
    "lang": "en"
  },
  {
    "questions": "کام تاقیکردنەوە لە قاڵای A ئەنجام دەدرێن؟",
    "command": "select lecture_id from final_exam_schedule where location_id = (select location_id from exam_locations where location_name = 'Hall A');",
    "lang": "ku"
  },
  {
    "questions": "List all final exam rules.",
    "command": "select rule_description from exam_rules;",
    "lang": "en"
  },
  {
    "questions": "هەموو یاساکانی تاقیکردنەوەی کۆتایی پێشانی بدە.",
    "command": "select rule_description from exam_rules;",
    "lang": "ku"
  },
  {
    "questions": "What is rule number 5 for exams?",
    "command": "select rule_description from exam_rules where rule_id = 5;",
    "lang": "en"
  },
  {
    "questions": "یاسای ژمارە ٥ی تاقیکردنەوە چییە؟",
    "command": "select rule_description from exam_rules where rule_id = 5;",
    "lang": "ku"
  },
  {
    "questions": "Which staff member is supervising all exams in Hall B?",
    "command": "select distinct staff_id from final_exam_schedule where location_id = (select location_id from exam_locations where location_name = 'Hall B');",
    "lang": "en"
  },
  {
    "questions": "کام مامۆستا سەرپەرشتی هەموو تاقیکردنەوەکانی قاڵای B دەکات؟",
    "command": "select distinct staff_id from final_exam_schedule where location_id = (select location_id from exam_locations where location_name = 'Hall B');",
    "lang": "ku"
  },
  {
    "questions": "Which lectures have exams on January 5?",
    "command": "select lecture_id from final_exam_schedule where exam_date = '2025-01-05';",
    "lang": "en"
  },
  {
    "questions": "کام وانە تاقیکردنەوەیان لە ٥ی جەنەورییە؟",
    "command": "select lecture_id from final_exam_schedule where exam_date = '2025-01-05';",
    "lang": "ku"
  },
  {
    "questions": "Get final exams supervised by staff ID 3.",
    "command": "select * from final_exam_schedule where staff_id = 3;",
    "lang": "en"
  },
  {
    "questions": "هەموو تاقیکردنەوەی سەرپەرشتی مامۆستای ژمارە ٣ پیشان بدە.",
    "command": "select * from final_exam_schedule where staff_id = 3;",
    "lang": "ku"
  },
  {
    "questions": "List lectures with exams in Semester 2.",
    "command": "select lecture_id from final_exam_schedule where semester_id = (select semester_id from semesters where semester_name = 'Semester 2');",
    "lang": "en"
  },
  {
    "questions": "وانەکانی سەمێستەری دووەم کە تاقیکردنەوەیان هەیە پێشانی بدە.",
    "command": "select lecture_id from final_exam_schedule where semester_id = (select semester_id from semesters where semester_name = 'Semester 2');",
    "lang": "ku"
  },
  {
    "questions": "What rules apply to electronic devices during exams?",
    "command": "select rule_description from exam_rules where rule_description ILIKE '%electronic%';",
    "lang": "en"
  },
  {
    "questions": "کام یاسا بە سەبارەت بە ئامێرە ئەلیکترۆنییەکانە لەکاتی تاقیکردنەوەدا؟",
    "command": "select rule_description from exam_rules where rule_description ILIKE '%electronic%';",
    "lang": "ku"
  },
  {
    "questions": "Are there any exams scheduled on a Friday?",
    "command": "select * from final_exam_schedule where extract(dow from exam_date) = 5;",
    "lang": "en"
  },
  {
    "questions": "هەر تاقیکردنەوەیەک هەیە لە ڕۆژی هەینی؟",
    "command": "select * from final_exam_schedule where extract(dow from exam_date) = 5;",
    "lang": "ku"
  },
  {
    "questions": "Which exam location has the most scheduled exams?",
    "command": "select location_id, count(*) as total_exams from final_exam_schedule group by location_id order by total_exams desc limit 1;",
    "lang": "en"
  },
  {
    "questions": "کام شوێنی تاقیکردنەوە زۆرترین تاقیکردنەوەی هەیە؟",
    "command": "select location_id, count(*) as total_exams from final_exam_schedule group by location_id order by total_exams desc limit 1;",
    "lang": "ku"
  },
  {
    "questions": "Which lecture has the latest scheduled exam?",
    "command": "select lecture_id from final_exam_schedule order by exam_date desc, exam_time desc limit 1;",
    "lang": "en"
  },
  {
    "questions": "کام وانە دوایین تاقیکردنەوەی هەیە لە خشتەکەدا؟",
    "command": "select lecture_id from final_exam_schedule order by exam_date desc, exam_time desc limit 1;",
    "lang": "ku"
  },
  {
    "questions": "Show all final exams in Room 101.",
    "command": "select * from final_exam_schedule where location_id = (select location_id from exam_locations where location_name = 'Room 101');",
    "lang": "en"
  },
  {
    "questions": "هەموو تاقیکردنەوەکانی ناو ژووری ١٠١ نیشان بدە.",
    "command": "select * from final_exam_schedule where location_id = (select location_id from exam_locations where location_name = 'Room 101');",
    "lang": "ku"
  },
  {
    "questions": "List all lectures that have no scheduled final exams.",
    "command": "select * from lectures where lecture_id not in (select lecture_id from final_exam_schedule);",
    "lang": "en"
  },
  {
    "questions": "هەموو وانەی بێ تاقیکردنەوەی کۆتایی پێشانی بدە.",
    "command": "select * from lectures where lecture_id not in (select lecture_id from final_exam_schedule);",
    "lang": "ku"
  },
  {
    "questions": "Find exams that start at or after 3 PM.",
    "command": "select * from final_exam_schedule where exam_time >= '15:00:00';",
    "lang": "en"
  },
  {
    "questions": "تاقیکردنەوەکان بدۆزەوە کە لە ٣ی ئەوارە پەیوەندیدارن.",
    "command": "select * from final_exam_schedule where exam_time >= '15:00:00';",
    "lang": "ku"
  },
  {
    "questions": "Count the number of exams scheduled per day.",
    "command": "select exam_date, count(*) as total_exams from final_exam_schedule group by exam_date;",
    "lang": "en"
  },
  {
    "questions": "ژمارەی تاقیکردنەوە لە هەر ڕۆژێکدا بۆ ماوەکانیان پێشانی بدە.",
    "command": "select exam_date, count(*) as total_exams from final_exam_schedule group by exam_date;",
    "lang": "ku"
  },
  {
    "questions": "Which rule mentions 'calculator'?",
    "command": "select * from exam_rules where rule_description ILIKE '%calculator%';",
    "lang": "en"
  },
  {
    "questions": "کام یاسا باس لە 'hesabkar' دەکات؟",
    "command": "select * from exam_rules where rule_description ILIKE '%calculator%';",
    "lang": "ku"
  },
  {
    "questions": "List all locations used in Semester 1.",
    "command": "select distinct location_id from final_exam_schedule where semester_id = (select semester_id from semesters where semester_name = 'Semester 1');",
    "lang": "en"
  },
  {
    "questions": "هەموو شوێنەکان کە لە سەمێستەری یەکەم بەکاردەهێنرێن نیشان بدە.",
    "command": "select distinct location_id from final_exam_schedule where semester_id = (select semester_id from semesters where semester_name = 'Semester 1');",
    "lang": "ku"
  },
  {
    "questions": "Get exam dates where more than 5 exams are scheduled.",
    "command": "select exam_date from final_exam_schedule group by exam_date having count(*) > 5;",
    "lang": "en"
  },
  {
    "questions": "وەکاتی تاقیکردنەوەکان پیشان بدە کە زیاتر لە 5 تاقیکردنەوەیان هەیە.",
    "command": "select exam_date from final_exam_schedule group by exam_date having count(*) > 5;",
    "lang": "ku"
  },
  {
    "questions": "Find lectures that are held in Semester 2 but not in Semester 1.",
    "command": "select * from lectures where semester_id = (select semester_id from semesters where semester_name = 'Semester 2') and lecture_id not in (select lecture_id from lectures where semester_id = (select semester_id from semesters where semester_name = 'Semester 1'));",
    "lang": "en"
  },
  {
    "questions": "وانەکانی سەمێستەری دووەم بدۆزەوە کە لە یەکەم نیین.",
    "command": "select * from lectures where semester_id = (select semester_id from semesters where semester_name = 'Semester 2') and lecture_id not in (select lecture_id from lectures where semester_id = (select semester_id from semesters where semester_name = 'Semester 1'));",
    "lang": "ku"
  },
  {
    "questions": "Which semester has the most lectures?",
    "command": "select semester_id from lectures group by semester_id order by count(*) desc limit 1;",
    "lang": "en"
  },
  {
    "questions": "کام سەمێستر زۆرترین وانە هەیە؟",
    "command": "select semester_id from lectures group by semester_id order by count(*) desc limit 1;",
    "lang": "ku"
  },
  {
    "questions": "List all teachers who do not teach any lectures.",
    "command": "select * from teachers where teacher_id not in (select teacher_id from lectures);",
    "lang": "en"
  },
  {
    "questions": "هەموو مامۆستایەکان پیشان بدە کە هیچ وانەیەک ناڵێنەوە.",
    "command": "select * from teachers where teacher_id not in (select teacher_id from lectures);",
    "lang": "ku"
  },
  {
    "questions": "Show exam rules.",
    "command": "select * from exam_rules order by length(rule_description) desc;",
    "lang": "en"
  },
  {
    "questions": "یاساکانی تاقیکردنەوە پێشان بدە.",
    "command": "select * from exam_rules order by length(rule_description) desc;",
    "lang": "ku"
  },
  {
    "questions": "Find the most frequently used exam location.",
    "command": "select location_id from final_exam_schedule group by location_id order by count(*) desc limit 1;",
    "lang": "en"
  },
  {
    "questions": "باوترین شوێنی تاقیکردنەوە بدۆزەوە.",
    "command": "select location_id from final_exam_schedule group by location_id order by count(*) desc limit 1;",
    "lang": "ku"
  },
  {
    "questions": "Which lectures are repeated in multiple semesters?",
    "command": "select lecture_name from lectures group by lecture_name having count(distinct semester_id) > 1;",
    "lang": "en"
  },
  {
    "questions": "کام وانە لە چەند سەمێستەرەوە دووبارە دەبێتەوە؟",
    "command": "select lecture_name from lectures group by lecture_name having count(distinct semester_id) > 1;",
    "lang": "ku"
  }
]
]

qdrant_builder(datasets)