--colleges table----------------------------------------------------------
create table colleges(
    college_id serial primary key,
    name text not null,
    dean text not null,
    dean_id int,
    college_email text,
    location text,
    building_number int,
    description text,
    website_url text,
    establishment_year int
);

insert into colleges(name, dean, dean_id, college_email, location, building_number, description, website_url, establishment_year)values
('College of engineering', 'Dr. Serwan Khurshid Rafiq Al Zahawi', 1, 'eng@univsul.edu.iq',
'College of Engineering, University of Sulaimani (New Campus), Tasluja Street 1, Zone 501, Sulaymaniyah', 4, 'College of Engineering produces well-qualified engineering graduates who are ready for immediate and productive entry into the workforce.',
'https://eng.univsul.edu.iq/https://eng.univsul.edu.iq/https://eng.univsul.edu.iq/https://eng.univsul.edu.iq/', 1968);


--engineering departments table---------------------------------------------
create table engineering_departments(
    department_id serial primary key,
    department_name text not null,
    department_head text not null,
    department_head_id int,
    department_description text,
    duration text
);

insert into engineering_departments(department_name, department_head, department_head_id, department_description, duration)values
('Computer engineering', 'Shwan Chatto Abdulla', 2, 'The department demonstrates a comprehensive understanding and practical application of core principles and technologies in the field of Computer Engineering, such as: Artificial Intelligence, Computer Architecture, Digital Logic Circuits, Microprocessors, Mathematics, Robotics, Digital Communication, Operating Systems, Control Systems, Electric Circuit, Engineering Management, database systems, Software Engineering, and Information Technology.', 
'- Our program spans a total of 8 Semesters
- Each academic year is divided into two semesters
- Each semester comprises 15 Weeks of studying'),
('Electrical Engineering', 'Dr. Jwan Satei Raafat', 3, 'The Department of Electrical Engineering is dedicated to delivering high-quality instruction that aligns with the latest challenges and developments in electrical engineering education. Our primary goal is to develop future leaders who will drive innovation and excel in the factories and industries of our region.',
'- Our program spans a total of 8 semesters
- with each academic year divided into two semesters
- Each semester comprises 15 weeks of studying'),
('Architecture Engineering', 'Prof. Dr. Abdullah Y. Tayib Shkak', 4, 'Our department envisions a harmonious integration of architecture, structural studies, theory, and design. We strive to equip our graduates with the necessary tools to actively engage in the dynamic and ever-evolving architectural landscape, anticipating and embracing paradigm shifts, and effectively responding to changes in local, national, and international communities.', '- Our program spans a total of 10 semesters
- With each academic year divided into two semesters
- Each semester comprises 15 weeks of studying'),
('Civil Engineering', 'Asst. Prof. Dr. Yaseen Ahmed Hama Amin ', 5, 'By combining rigorous academic instruction with practical experiences, we strive to produce graduates who are not only well-versed in their subject matter but also adept at problem-solving and critical thinking. Our ultimate goal is to empower our students to become competent, confident professionals ready to make a positive impact in their respective industries.', '- Our program spans a total of 8 semesters
- with each academic year divided into two semesters
- Each semester comprises 15 weeks of studying'),
('Water Resources Engineering', 'Prof. Nihad Bahaaldeen Salih Baban', 6, 'graduates are equipped with a diverse skill set that enables them to address a wide range of engineering challenges from multiple perspectives. They possess expertise in various areas, including irrigation, soils, water resources studies and management, and drainage design. This comprehensive knowledge allows them to contribute to the development and preservation of water resources for future generations, while also safeguarding water from pollution.', '- Our program spans a total of 8 semesters
- with each academic year divided into two semesters
- Each semester comprises 15 weeks of studying');



--staff table------------------------------------------------------------

create table engin_staff(
    staff_member_id serial primary key,
    name text not null,
    position text,
    email text,
    department_id int references engineering_departments(department_id)
);

insert into engin_staff(name, position, email, department_id)values
('Dr. Serwan Khurshid Rafiq Al Zahawi', 'Dean of engineering college, and Lecturer with a PhD degree in Structural engineering', 'serwan.rafiq@univsul.edu.iq', 3),
('Dr. Shwan Chatto Abdulla', 'Head and Lecturer of computer engineering department', 'shwan.abdullah@univsul.edu.iq', 1),
('Dr. Jwan Satei Raafat', 'Head and Lecturer of Electrical Engineering department', 'jwan.raafat@univsul.edu.iq', 2),
('Prof. Dr. Abdullah Y. Tayib Shkak', 'Head and Lecturer of Architecture Engineering department', 'abdullah.tayib@univsul.edu.iq', 3),
('Asst. Prof. Dr. Yaseen Ahmed Hama Amin', 'Head and Lecturer of Civil Engineering department', 'yassen.amin@univsul.edu.iq', 4),
('Prof. Nihad Bahaaldeen Salih Baban', 'Head and Lecturer of Water Resources Engineering department', 'nihad.salih@univsul.edu.iq', 5),
('Dr. Jaza Faiq Gul-Mohammed', 'Lecturer in Computer engineering department', 'jaza.gul@univsul.edu.iq', 1),
('Mr. Rizgar Ahmed Salih', 'Decider and Lecturer of Computer engineering department', 'rizgar.salih@univsul.edu.iq', 1),
('Mr. Twana Saeed Ali', 'Lecturer in computer engineering department, and Directorate of IT and Training', 'twana.ali@univsul.edu.iq', 1),
('Mr. Sarwat Ali Ahmed', 'Lecturer in computer engineering department', 'sarwat.hussein@univsul.edu.iq', 1),
('Dr. Taymaa Hussein Ali', 'Lecturer in egnineering', 'taymaa.ali@univsul.edu.iq', 1),
('Ms. Shelan Raheem Ibrahim', 'Lecturer in engineering', 'shelan.ibrahim@univsul.edu.iq', 1),
('Mr. Mohammed Abdalla Ali', 'Lecturer in computer engineering department', 'mohammed.karamwais@univsul.edu.iq', 1);



--years table------------------------------------------------------------

create table academic_years(
    year_id serial primary key,
    year_name text not null
);

insert into academic_years(year_name)values
('First Year'),('Second Year'),('Third Year'),('Fourth Year'),('Fifth Year');



--semesters table----------------------------------------------------------

create table semesters(
    semester_id serial primary key,
    semester_number int not null,
    year_id int references academic_years(year_id),
    semester_name text
);

insert into semesters(semester_number, year_id)values
(1,1), (2,1), (3,2), (4,2), (5,3), (6,3), (7,4), (8,4), (9,5), (10,5);



--lectures table-----------------------------------------------------------

create table lectures(
    lecture_id serial primary key,
    lecture_title text not null,
    department_id int references engineering_departments(department_id),
    year_id int references academic_years(year_id),
    semester_id int references semesters(semester_id),
    description text,
    note text,
    weekly_hours int
);

insert into lectures(lecture_title, department_id, year_id, semester_id)values
('Electrical Circuits', 1, 1, 1),('Computer Fandamentals', 1, 1, 1), ('Calculus 1', 1, 1, 1), ('English Language Level 1', 1, 1, 1),
('Kurdology', 1, 1, 1), ('University Work Environment', 1, 1, 1), ('English Language Level 2', 1, 1, 2),('Programming Concepts and Algorithms', 1, 1, 2), ('Logic Design 1', 1, 1, 2)
,('Physical Electronics', 1, 1, 2), ('Professional Skills', 1, 1, 2), ('Calculus 2', 1, 1, 2), ('Physical Education', 1, 1, 2), ('Electronic Circuits', 1, 2, 3), ('Logic Design 2', 1, 2, 3),
('Computer Programing(C language) 1', 1, 2, 3), ('Database Systems 1', 1, 2, 3), ('Elective(Engineering analysis)', 1, 2, 3),
('Computer Architecture 1', 1, 2, 4), ('Computer Programing(C Language) 2', 1, 2, 4), ('Object-Oriented Programing', 1, 2, 4),
('Computer Networks 1', 1, 2, 4), ('Probability and Statistics', 1, 2, 4);



--lecture and lecturer table-----------------------------------------------

create table lecturers(
    lecturer_id int references engin_staff(staff_member_id),
    lecture_id int references lectures(lecture_id),
    note text
);

insert into lecturers(lecturer_id, lecture_id)values
(10, 1), (9, 2), (8, 3),
(11, 4), (12, 5), ( 11, 7),
(13, 8), (8, 8), (10, 9), (1, 9),
(10, 10),
(7 , 12);

insert into lecturers(lecture_id, note)values
(6, 'undetermined yet'),(11, 'undetermined yet'),(13, 'undetermined yet');


--guides----------------------------------------------------------------




create table guide(
    guide_id serial primary key,
    department_id int references engineering_departments(department_id),
    title text not null,
    content text not null
);

insert into guide(title, content)values
('forgot university email password', 'just go to your department head and and tell him about that. he will solve you problem'),
('how to ask for a day off', 'If you are sik first go to tomar they will give a paper you take it to the helth senter they 
will sign it for you then you take it back to the tomar');


--