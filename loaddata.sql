CREATE TABLE "Users" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "first_name" varchar,
  "last_name" varchar,
  "email" varchar,
  "bio" varchar,
  "username" varchar,
  "password" varchar,
  "profile_image_url" varchar,
  "created_on" date,
  "active" bit
);

CREATE TABLE "DemotionQueue" (
  "action" varchar,
  "admin_id" INTEGER,
  "approver_one_id" INTEGER,
  FOREIGN KEY(`admin_id`) REFERENCES `Users`(`id`),
  FOREIGN KEY(`approver_one_id`) REFERENCES `Users`(`id`),
  PRIMARY KEY (action, admin_id, approver_one_id)
);


CREATE TABLE "Subscriptions" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "follower_id" INTEGER,
  "author_id" INTEGER,
  "created_on" date,
  FOREIGN KEY(`follower_id`) REFERENCES `Users`(`id`),
  FOREIGN KEY(`author_id`) REFERENCES `Users`(`id`)
);

CREATE TABLE "Posts" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "category_id" INTEGER,
  "title" varchar,
  "publication_date" date,
  "image_url" varchar,
  "content" varchar,
  "approved" bit,
  FOREIGN KEY(`user_id`) REFERENCES `Users`(`id`)
);

CREATE TABLE "Comments" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "post_id" INTEGER,
  "author_id" INTEGER,
  "content" varchar,
  FOREIGN KEY(`post_id`) REFERENCES `Posts`(`id`),
  FOREIGN KEY(`author_id`) REFERENCES `Users`(`id`)
);

CREATE TABLE "Reactions" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "label" varchar,
  "image_url" varchar
);

CREATE TABLE "PostReactions" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "reaction_id" INTEGER,
  "post_id" INTEGER,
  FOREIGN KEY(`user_id`) REFERENCES `Users`(`id`),
  FOREIGN KEY(`reaction_id`) REFERENCES `Reactions`(`id`),
  FOREIGN KEY(`post_id`) REFERENCES `Posts`(`id`)
);

CREATE TABLE "Tags" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "label" varchar
);

CREATE TABLE "PostTags" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "post_id" INTEGER,
  "tag_id" INTEGER,
  FOREIGN KEY(`post_id`) REFERENCES `Posts`(`id`),
  FOREIGN KEY(`tag_id`) REFERENCES `Tags`(`id`)
);

CREATE TABLE "Categories" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "label" varchar
);

INSERT INTO Categories ('label') VALUES ('News');
INSERT INTO Tags ('label') VALUES ('JavaScript');
INSERT INTO Tags ('label') VALUES ('Python');
INSERT INTO Tags ('label') VALUES ('React');
INSERT INTO Tags ('label') VALUES ('Node.js');
INSERT INTO Tags ('label') VALUES ('CSS');
INSERT INTO Tags ('label') VALUES ('HTML');
INSERT INTO Tags ('label') VALUES ('SQL');
INSERT INTO Tags ('label') VALUES ('Web Development');
INSERT INTO Tags ('label') VALUES ('Tutorial');
INSERT INTO Tags ('label') VALUES ('Opinion');
INSERT INTO Reactions ('label', 'image_url') VALUES ('happy', 'https://pngtree.com/so/happy');


ALTER TABLE "Users" ADD "type" varchar;

DELETE FROM "Users";


INSERT INTO Categories ('label') VALUES ('Work'), ('Hobby'), ('Fluff');

UPDATE Categories SET 'label' = 'Life' WHERE id = 1;

-- Seed Users
INSERT INTO Users ('first_name', 'last_name', 'email', 'bio', 'username', 'password', 'profile_image_url', 'created_on', 'active', 'type') 
VALUES 
('John', 'Doe', 'john@example.com', 'Software developer and tech enthusiast', 'johndoe', 'password123', 'https://example.com/john.jpg', '2024-01-15', 1, 'author'),
('Jane', 'Smith', 'jane@example.com', 'Full-stack developer', 'janesmith', 'password123', 'https://example.com/jane.jpg', '2024-01-20', 1, 'author'),
('Bob', 'Johnson', 'bob@example.com', 'Database administrator', 'bobjohnson', 'password123', 'https://example.com/bob.jpg', '2024-02-01', 1, 'admin'),
('Alice', 'Williams', 'alice@example.com', 'Frontend specialist', 'alicew', 'password123', 'https://example.com/alice.jpg', '2024-02-05', 1, 'author'),
('Charlie', 'Brown', 'charlie@example.com', 'DevOps engineer', 'charlieb', 'password123', 'https://example.com/charlie.jpg', '2024-02-10', 1, 'author');

-- Seed Posts
INSERT INTO Posts ('user_id', 'category_id', 'title', 'publication_date', 'image_url', 'content', 'approved') 
VALUES 
(1, 1, 'Getting Started with Python', '2024-02-01', 'https://example.com/python.jpg', 'Python is a great language for beginners...', 1),
(1, 2, 'My Side Project Journey', '2024-02-05', 'https://example.com/project.jpg', 'Here is how I built my first web app...', 1),
(2, 1, 'React Best Practices', '2024-02-08', 'https://example.com/react.jpg', 'Learn the best practices for React development...', 1),
(2, 3, 'Coding Memes That Made Me Laugh', '2024-02-10', 'https://example.com/memes.jpg', 'Here are my favorite coding memes...', 1),
(4, 1, 'CSS Grid vs Flexbox', '2024-02-12', 'https://example.com/css.jpg', 'When to use CSS Grid and when to use Flexbox...', 1),
(5, 2, 'Building a CI/CD Pipeline', '2024-02-13', 'https://example.com/cicd.jpg', 'Step-by-step guide to setting up CI/CD...', 0),
(1, 1, 'Advanced SQL Queries', '2024-02-14', 'https://example.com/sql.jpg', 'Master complex SQL queries with these tips...', 0);

-- Seed Comments
INSERT INTO Comments ('post_id', 'author_id', 'content') 
VALUES 
(1, 2, 'Great introduction! Very helpful for beginners.'),
(1, 4, 'Thanks for sharing. I learned a lot.'),
(2, 5, 'Inspiring story! Keep it up.'),
(3, 1, 'These tips are gold. Thank you!'),
(3, 4, 'I disagree with point #3, but overall great article.'),
(4, 1, 'Haha, the semicolon one got me!'),
(5, 1, 'Perfect timing! I was just learning about this.');

-- Seed more Reactions
INSERT INTO Reactions ('label', 'image_url') VALUES 
('heart', 'https://example.com/heart.png'),
('laugh', 'https://example.com/laugh.png'),
('mind-blown', 'https://example.com/mindblown.png'),
('fire', 'https://example.com/fire.png');

-- Seed PostReactions
INSERT INTO PostReactions ('user_id', 'reaction_id', 'post_id') 
VALUES 
(2, 1, 1),
(4, 1, 1),
(5, 2, 1),
(1, 1, 3),
(3, 5, 3),
(1, 3, 4),
(2, 3, 4),
(3, 3, 4),
(1, 5, 5),
(2, 5, 5);

-- Seed PostTags
INSERT INTO PostTags ('post_id', 'tag_id') 
VALUES 
(1, 2),
(1, 9),
(2, 2),
(2, 8),
(3, 3),
(3, 8),
(4, 10),
(5, 5),
(5, 6),
(5, 8),
(6, 4),
(6, 8),
(7, 7),
(7, 9);

-- Seed Subscriptions
INSERT INTO Subscriptions ('follower_id', 'author_id', 'created_on') 
VALUES 
(2, 1, '2024-02-02'),
(4, 1, '2024-02-03'),
(5, 1, '2024-02-04'),
(1, 2, '2024-02-06'),
(4, 2, '2024-02-07'),
(1, 4, '2024-02-11'),
(2, 4, '2024-02-12'),
(1, 5, '2024-02-13');

-- Seed DemotionQueue
INSERT INTO DemotionQueue ('action', 'admin_id', 'approver_one_id') 
VALUES 
('demote', 3, 1);




            SELECT
                p.id,
                p.title,
                p.publication_date,
                u.first_name || ' ' || u.last_name AS author,
                c.label AS category,
                pt.id,
                pt.post_id,
                pt.tag_id,
                t.id,
                t.label
            FROM Posts p
            JOIN Users u
                ON u.id = p.user_id
            JOIN Categories c
                ON c.id = p.category_id
            JOIN PostTags pt
                ON pt.post_id = p.id
            JOIN Tags t
                ON pt.tag_id = t.id
            WHERE p.approved = 1
            AND date(p.publication_date) <= date('now')
            ORDER BY date(p.publication_date) DESC

SELECT
    p.id,
    p.title,
    p.publication_date,
    u.first_name || ' ' || u.last_name AS author,
    c.label AS category,
    GROUP_CONCAT(t.label, ', ') AS tags
FROM Posts p
JOIN Users u ON u.id = p.user_id
JOIN Categories c ON c.id = p.category_id
LEFT JOIN PostTags pt ON pt.post_id = p.id
LEFT JOIN Tags t ON pt.tag_id = t.id
WHERE p.approved = 1
AND date(p.publication_date) <= date('now')
GROUP BY p.id, p.title, p.publication_date, u.first_name, u.last_name, c.label
ORDER BY date(p.publication_date) DESC


SELECT
    p.id,
    p.title,
    p.publication_date,
    u.first_name || ' ' || u.last_name AS author,
    c.label AS category,
    json_group_array(
        json_object('id', t.id, 'label', t.label)
    ) AS tags
FROM Posts p
JOIN Users u ON u.id = p.user_id
JOIN Categories c ON c.id = p.category_id
LEFT JOIN PostTags pt ON pt.post_id = p.id
LEFT JOIN Tags t ON pt.tag_id = t.id
WHERE p.approved = 1
AND date(p.publication_date) <= date('now')
GROUP BY p.id
ORDER BY date(p.publication_date) DESC