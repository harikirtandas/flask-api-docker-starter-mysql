-- Este script solo corre en el PRIMER arranque del volumen mysql-data
-- (docker-entrypoint-initdb.d se ejecuta una unica vez, cuando /var/lib/mysql
-- esta vacio). Para reaplicarlo hace falta recrear el volumen: make fresh
--
-- Es el schema del vertical slice demo (auth JWT + notas). En un proyecto real
-- se reemplaza entero por el schema propio, o se agregan archivos .sql
-- numerados (02-..., 03-...) y se aplican con:
--   make db-import FILE=docker/mysql/init/0N-....sql

CREATE TABLE IF NOT EXISTS usuarios (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre        VARCHAR(120)  NOT NULL,
    email         VARCHAR(180)  NOT NULL UNIQUE,
    password_hash VARCHAR(255)  NOT NULL,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- lista negra de JWT invalidados a mano (logout). El JWT en si es sin estado
-- (la firma alcanza para validarlo), asi que revocar antes de su "exp" natural
-- requiere guardar su "jti" en algun lado hasta que venza solo. Una fila vieja
-- (expira_en < NOW()) ya es inofensiva aunque no se borre; no hay job de
-- limpieza en este starter, se puede sumar un DELETE periodico si hace falta.
CREATE TABLE IF NOT EXISTS tokens_revocados (
    jti        CHAR(36) PRIMARY KEY,
    expira_en  DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS notas (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT UNSIGNED NOT NULL,
    titulo     VARCHAR(120) NOT NULL,
    cuerpo     TEXT         NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Usuario demo: email demo@demo.test / password "secret".
-- Hash generado con werkzeug.security.generate_password_hash('secret', method='pbkdf2:sha256')
-- (pbkdf2 a proposito, no scrypt: scrypt pide el paquete opcional "scrypt" que
-- este starter no instala).
INSERT INTO usuarios (nombre, email, password_hash) VALUES
    ('Usuario Demo', 'demo@demo.test', 'pbkdf2:sha256:1000000$HRt3CmCcJ4Vns6zm$e342209298b137fc6079929a6f58d901d5720f08569c2436559bbd507275aaf5');

INSERT INTO notas (usuario_id, titulo, cuerpo) VALUES
    (1, 'Primera nota', 'Cuerpo de ejemplo de la primera nota.'),
    (1, 'Segunda nota', 'Cuerpo de ejemplo de la segunda nota.');
