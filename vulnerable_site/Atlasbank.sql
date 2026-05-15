
CREATE DATABASE IF NOT EXISTS atlasbank_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE atlasbank_db;

DROP TABLE IF EXISTS demandes;

CREATE TABLE demandes (
    id            INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    nom           VARCHAR(100)    NOT NULL,
    prenom        VARCHAR(100)    NOT NULL,
    email         VARCHAR(150)    NOT NULL,
    telephone     VARCHAR(30)     NOT NULL,
    cin           VARCHAR(30)     NOT NULL,
    adresse       VARCHAR(255)    NOT NULL,
    ville         VARCHAR(80)     NOT NULL,
    profession    VARCHAR(120)    NOT NULL,
    revenu        DECIMAL(12,2)   DEFAULT 0.00,
    type_compte   VARCHAR(60)     NOT NULL,
    message       TEXT            DEFAULT NULL,
    date_demande  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


INSERT INTO demandes (nom, prenom, email, telephone, cin, adresse, ville, profession, revenu, type_compte, message, date_demande) VALUES
('El Fassi',    'Karim',   'karim.elfassi@gmail.com',  '+212 661 234 567', 'BK472810', '45 Rue Ibn Battouta', 'Casablanca',  'Ingénieur informatique', 12500.00, 'Compte Courant',       'Je souhaite une carte Visa Gold.', NOW()),
('Benali',      'Sara',    'sara.benali@outlook.com',  '+212 672 891 034', 'CD301245', '12 Avenue Hassan II',  'Rabat',       'Médecin généraliste',    22000.00, 'Compte Épargne',       NULL,                               NOW()),
('Tazi',        'Mohamed', 'm.tazi@entreprise.ma',     '+212 655 100 200', 'AB123456', '7 Boulevard Zerktouni','Marrakech',   'Gérant PME',             35000.00, 'Compte Professionnel', 'Domiciliation société SARL.',       NOW());

SELECT * FROM demandes;