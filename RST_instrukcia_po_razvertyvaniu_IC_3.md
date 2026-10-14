**Содержание**

[**Введение 2**](#введение)

> [Цель инструкции 2](#цель-инструкции)
>
> [Общие сведения 2](#общие-сведения)
>
> [Термины и определения 3](#термины-и-определения)

[**Backend 8**](#backend)

> [1.1. Nginx 8](#nginx)
>
> [1.2. PHP-FPM и расширения 8](#php-fpm-и-расширения)
>
> [1.3. Создание и настройка каталога Backend
> 9](#создание-и-настройка-каталога-backend)
>
> [1.4. Настройка переменных окружения
> 9](#настройка-переменных-окружения)
>
> [1.5. Composer 9](#composer)
>
> [1.6. PostgreSQL 10](#postgresql)
>
> [1.7. Миграции 11](#миграции)
>
> [1.8. Apache FOP 11](#apache-fop)
>
> [1.9. RabbitMQ 12](#rabbitmq)
>
> [1.10. Сrontab 12](#сrontab)

[**Frontend 12**](#frontend)

> [2.1. Node.js 12](#node.js)
>
> [2.2. Создание и настройка каталога Frontend
> 13](#создание-и-настройка-каталога-frontend)
>
> [2.3. Настройка переменных окружения
> 13](#настройка-переменных-окружения-1)
>
> [2.4. Зависимости 14](#зависимости)
>
> [2.5. Запуск приложения: 14](#запуск-приложения)

[**Machine Learning 14**](#machine-learning)

> [3.1. Пакеты и языковые модели 14](#пакеты-и-языковые-модели)
>
> [3.2. Python 14](#python)
>
> [3.3. Создание и настройка ML-каталога
> 15](#создание-и-настройка-ml-каталога)
>
> [3.4. PM2 16](#pm2)
>
> [3.5. Запуск приложения 16](#запуск-приложения-1)
>
> [3.6. Видеодрайвер 16](#видеодрайвер)
>
> [3.7. Перезапуск сервисов 16](#перезапуск-сервисов)

# **Введение**

## **Цель инструкции**

<span class="mark">Цель данной инструкции – предоставить пошаговые
руководства по установке и настройке необходимых компонентов для работы
backend, frontend, ML и базы данных на Debian 11. Этот документ
охватывает все аспекты настройки, начиная от установки необходимых
пакетов и заканчивая настройкой конфигурационных файлов и запуском
приложений.</span>

## **Общие сведения**

Проект состоит из трех основных компонентов: backend, frontend и ML.
Каждый из этих компонентов выполняет свою специфическую роль и
взаимодействует с другими компонентами для обеспечения общей
функциональности системы.

Backend предоставляет API на Symfony, взаимодействует с базой данных
PostgreSQL и использует RabbitMQ для управления очередями сообщений.
Frontend разработан на Nuxt.js и взаимодействует с backend через
HTTP-запросы. ML состоит из нескольких моделей машинного обучения,
которые анализируют данные и взаимодействуют с backend для получения и
отправки результатов.

Все компоненты системы взаимосвязаны и работают вместе для обеспечения
комплексного решения, которое включает в себя обработку запросов,
управление данными, анализ данных и отображение интерфейса пользователя

## **Термины и определения**

<table>
<colgroup>
<col style="width: 17%" />
<col style="width: 82%" />
</colgroup>
<tbody>
<tr class="odd">
<td><blockquote>
<p>Backend</p>
</blockquote></td>
<td><blockquote>
<p>Серверная часть приложения, которая обрабатывает запросы
пользователей, управляет базой данных и взаимодействует с другими
сервисами.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Frontend</p>
</blockquote></td>
<td><blockquote>
<p>Клиентская часть приложения, которая отображает интерфейс
пользователя и взаимодействует с серверной частью.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Machine Learning</p>
<p>(ML)</p>
</blockquote></td>
<td><blockquote>
<p>Область искусственного интеллекта, которая позволяет находить
закономерности и правила на основе примеров, создавая модель без
необходимости явного конкретного сценария для выполнения каждой
задачи.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Nginx</p>
</blockquote></td>
<td><blockquote>
<p>Веб-сервер, который обрабатывает HTTP-запросы и перенаправляет их к
серверной части приложения (backend). Он действует как посредник между
пользователем и сервером.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>PHP-FPM</p>
</blockquote></td>
<td><blockquote>
<p>Менеджер процессов для PHP, который управляет выполнением
PHP-скриптов. Он позволяет серверу эффективно обрабатывать множество
запросов одновременно.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Composer</p>
</blockquote></td>
<td><blockquote>
<p>Инструмент для управления зависимостями в PHP-проектах. Он
автоматически устанавливает и обновляет все необходимые библиотеки и
пакеты.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Apache FOP</p>
</blockquote></td>
<td><blockquote>
<p>Инструмент для форматирования документов в формате PDF. Он позволяет
создавать и изменять PDF-документы на основе XML-данных.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>RabbitMQ</p>
</blockquote></td>
<td><blockquote>
<p>Система управления очередями сообщений, которая позволяет приложениям
обмениваться сообщениями асинхронно. Это полезно для обработки задач в
фоновом режиме.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Crontab</p>
</blockquote></td>
<td><blockquote>
<p>Утилита для планирования задач в Unix-подобных операционных системах.
Она позволяет автоматически выполнять задачи в заданное время.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Node.js</p>
</blockquote></td>
<td><blockquote>
<p>Платформа для выполнения JavaScript на сервере. Она позволяет
разработчикам использовать JavaScript для создания серверных
приложений.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>PM2</p>
</blockquote></td>
<td><blockquote>
<p>Менеджер процессов для Node.js, который помогает управлять и
мониторить Node.js-приложения, обеспечивая их стабильную работу.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>PostgreSQL</p>
</blockquote></td>
<td><blockquote>
<p>Реляционная система управления базами данных, которая позволяет
хранить и управлять данными в структурированном виде.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>MySpell</p>
</blockquote></td>
<td><blockquote>
<p>Программа для проверки орфографии, которая помогает находить и
исправлять ошибки в тексте.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Python</p>
</blockquote></td>
<td><blockquote>
<p>Высокоуровневый язык программирования, который используется для
разработки различных приложений, включая веб-приложения, анализ данных и
машинное обучение.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Virtual Environment</p>
</blockquote></td>
<td><blockquote>
<p>Изолированная среда для разработки и выполнения Python-приложений.
Она позволяет устанавливать и управлять зависимостями для конкретного
проекта без влияния на другие проекты.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Pip</p>
</blockquote></td>
<td><blockquote>
<p>Менеджер пакетов для Python, который устанавливает и управляет
библиотеками и зависимостями для Python-проектов.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>JEuclid</p>
</blockquote></td>
<td><blockquote>
<p>Плагин для Apache FOP, который используется для форматирования
математических выражений в PDF-документах.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>PHP</p>
</blockquote></td>
<td><blockquote>
<p>Основной язык программирования серверной части приложения, который
используется для создания динамических веб-страниц.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Symfony</p>
</blockquote></td>
<td><blockquote>
<p>Фреймворк для разработки веб-приложений на PHP, который предоставляет
структуру и инструменты для создания сложных веб-приложений.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Debian</p>
</blockquote></td>
<td><blockquote>
<p>Операционная система на базе Linux, которая используется для
серверных и настольных приложений. Она известна своей стабильностью и
безопасностью.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>APT</p>
</blockquote></td>
<td><blockquote>
<p>Система управления пакетами в Debian и её производных, которая
позволяет устанавливать, обновлять и удалять программное
обеспечение.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>GPG</p>
</blockquote></td>
<td><blockquote>
<p>Система шифрования и подписи данных, которая обеспечивает
безопасность и целостность данных при передаче.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>NVIDIA</p>
</blockquote></td>
<td><blockquote>
<p>Производитель графических процессоров и драйверов для них, которые
используются для ускорения вычислений и обработки графики.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>TensorFlow</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для машинного обучения, разработанная Google, которая
предоставляет инструменты для создания и обучения моделей машинного
обучения.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Pymorphy3</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для морфологического анализа русского языка, которая
помогает обрабатывать и анализировать текст на русском языке.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Python-Levenshtein</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для вычисления расстояния Левенштейна между строками,
которая используется для измерения различий между строками текста.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Pix2Tex</p>
</blockquote></td>
<td><blockquote>
<p>Инструмент для преобразования изображений в LaTeX-код, который
используется для создания математических формул и уравнений.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Latex2MathML</p>
</blockquote></td>
<td><blockquote>
<p>Инструмент для преобразования LaTeX-кода в MathML, который
используется для отображения математических формул в веб-браузерах.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Onnxruntime</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для выполнения моделей ONNX (Open Neural Network
Exchange), которая позволяет запускать модели машинного обучения на
различных платформах.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Natsort</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для естественной сортировки строк, которая позволяет
сортировать строки в порядке, который интуитивно понятен человеку.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Pika</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для работы с RabbitMQ на Python, которая позволяет
Python-приложениям взаимодействовать с системой управления очередями
сообщений.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Retry</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для повторного выполнения операций в случае ошибки,
которая помогает сделать приложения более устойчивыми к сбоям.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Pandas</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для анализа данных в Python, которая предоставляет
структуры данных и инструменты для их обработки и анализа.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Cnstd</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для работы с китайскими стандартами, которая помогает
обрабатывать и анализировать текст на китайском языке.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Pycld2</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для определения языка текста, которая помогает определить,
на каком языке написан текст.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Waitress</p>
</blockquote></td>
<td><blockquote>
<p>WSGI-сервер для Python, который позволяет запускать
Python-веб-приложения и обрабатывать HTTP-запросы.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Translate</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для перевода текста, которая помогает переводить текст с
одного языка на другой.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Pillow</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для работы с изображениями в Python, которая предоставляет
инструменты для открытия, манипуляции и сохранения изображений.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>PyEnchant</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для проверки орфографии в Python, которая помогает
находить и исправлять ошибки в тексте.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>EasyOCR</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для распознавания текста в изображениях, которая позволяет
извлекать текст из изображений и документов.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>PDF2Image</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для преобразования PDF-документов в изображения, которая
позволяет конвертировать страницы PDF в изображения.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><blockquote>
<p>Threaded</p>
</blockquote></td>
<td><blockquote>
<p>Библиотека для работы с потоками в Python, которая позволяет
выполнять несколько задач одновременно.</p>
</blockquote></td>
</tr>
<tr class="odd">
<td><blockquote>
<p>Flask</p>
</blockquote></td>
<td><blockquote>
<p>Микрофреймворк для разработки веб-приложений на Python, который
предоставляет простые и гибкие инструменты для создания
веб-приложений.</p>
</blockquote></td>
</tr>
</tbody>
</table>

# **Backend**

## **1.1. Nginx**

1.1.1 Установите Nginx с помощью команды:

apt install nginx

1.1.2. Включите и запустите Nginx:

> systemctl enable nginx && systemctl start nginx

1.1.3. Замените пользователя процесса (например, на mlt) в файле
конфигурации

> /etc/nginx/nginx.conf.

1.1.3. Создайте конфигурацию сайта в каталоге

> /etc/nginx/sites-enabled.

Пример настройки для Symfony можно найти
[здесь](https://symfony.com/doc/current/setup/web_server_configuration.html).

1.1.4. Перезапустите веб-сервер:

> systemctl restart nginx

## **1.2. PHP-FPM и расширения**

1.2.1. Установите необходимые зависимости для подключения репозиториев:

> apt install -y lsb-release ca-certificates apt-transport-https
> software-properties-common gnupg2

1.2.2. Добавьте адрес репозитория:

> echo "deb https://packages.sury.org/php/ \$(lsb_release -sc) main" \|
> tee /etc/apt/sources.list.d/sury-php.list

1.2.3. Добавьте ключ репозитория:

> wget -qO - https://packages.sury.org/php/apt.gpg \| apt-key add -

1.2.4. Обновите список пакетов:

> apt update

1.2.5. Установите PHP с расширениями:

> ~~aptitude install php8.2-fpm php8.2-common php8.2-intl php8.2-pgsql~~
> apt install php8.2-fpm php8.2-common php8.2-intl php8.2-pgsql
>
> php8.2-xml php8.2-zip php8.2-amqp

1.2.6. Настройте подходящего пользователя и группу (например, mlt) в
файле конфигурации

> /etc/php/8.2/fpm/pool.d/[<u>www.conf</u>](http://www.conf).

1.2.7. Настройте размер загрузки файлов и длительность выполнения
скриптов

nano /etc/php/8.2/fpm/php.ini.

1.2.8. Добавте пользователя в группу

> sudo usermod -aG www-data mlt



1.2.9. Перезапустите процесс:

systemctl enable php8.2-fpm && systemctl restart php8.2-fpm

## **1.3. Создание и настройка каталога Backend**

1.31. Создайте каталог сайта с правами пользователя. например,
/var/www/backend с пользователем и группой mlt:

sudo mkdir -p /var/www/backend

1.3.2. Изменение владельца и группы каталога:

> sudo chown -R mlt:mlt /var/www/backend

1.3.3. Установка прав доступа:

sudo chmod -R 755 /var/www/backend

1.3.5. Проверка прав доступа:

ls -ld /var/www/backend

1.3.6. Загрузите в каталог исходный код бекенда.

## **1.4. Настройка переменных окружения**

1.4.1. Скопируйте файл .env.example в .env.

cd /var/www/backend

<span class="mark">cp .env.example .env</span>

1.4.3. Откройте файл .env в текстовом редакторе и измените все
переменные на свои значения.

nano .env

## **1.5. Composer**

1.5.1. Установите Composer:

> php -r "copy('https://getcomposer.org/installer',
> 'composer-setup.php');"
>
> php composer-setup.php
>
> mv composer.phar /usr/local/bin/composer
>
> php -r "unlink('composer-setup.php');"

1.5.2. Из под пользователя сайта (например, mlt) перейдите в каталог
сайта.

1.5.3. Установите зависимости и проведите миграции:

composer install

## **1.6. PostgreSQL**

1.6.1. Установите PostgreSQL с помощью команды:

> sudo apt update
>
> sudo apt install postgresql

1.6.2. Переключитесь на пользователя postgres:

> sudo -i -u postgres

1.6.3. Создайте нового пользователя PostgreSQL (имя пользователя должно
совпадать с переменной окружения backend в env файле):

> createuser --interactive

1.6.4. Создайте новую базу данных (убедитесь, что имя пользователя и имя
базы данных совпадают с переменными окружения каталога backend в env
файле):

> createdb --owner=имя_пользователя имя_базы_данных

1.6.5. Откройте файл конфигурации postgresql.conf:

> nano /etc/postgresql/16/main/postgresql.conf

1.6.6. Найдите параметр listen_addresses и измените его значение на
нужный IP-адрес, например:

> listen_addresses = '192.168.120.221'

1.6.7. Откройте файл конфигурации pg_hba.conf:

> nano /etc/postgresql/16/main/pg_hba.conf

1.6.8. Добавьте строки для настройки доступа к базе данных, следуя
образцу из этого же файла. Например:

> host all all 192.168.120.221/32 md5

1.7.9. Перезапуск :

systemctl restart postgresql

1.7.10. Логи доступны для просмотра посмотреть в /var/logs/postgresql

## **1.7. Миграции**

1.7.1. Из под пользователя сайта (например, mlt) перейдите в каталог
сайта.

1.7.2. Убедитесь, что вы уже настроили PostgreSQL и .env для backend
(заменить имя_пользователя, имя_бд на свои значения):

psql -U имя_пользователя -d имя_бд -h 192.168.120.221 -W

cat .env

1.7.3. Проведите миграции через консоль

> php bin/console cache:clear
>
> php bin/console cache:warmup
>
> php bin/console --no-interaction doctrine:migrations:migrate

## **1.8. Apache FOP**

1.7.1. Скачайте FOP с официального сайта: [Apache
FOP](https://xmlgraphics.apache.org/fop/download.html).

1.7.2. Распакуйте архив в удобное место, например: /etc/fop.conf.d/fop/.

> sudo mkdir -p /etc/fop.conf.d/fop/
>
> #sudo tar -xvf fop-\<version\>.tar.gz -C /etc/fop.conf.d/fop/
> sudo tar -xzf fop-2.11-bin.tar.gz \
  -C /etc/fop.conf.d/fop/ \
  --strip-components=2
распаковываем только каталог fop, который только на втором уровне вложенности fop-2.11-bin.tar.gz/utar://fop-2.11/fop
1.7.3. Скачайте JEuclid с
[SourceForge](https://sourceforge.net/projects/jeuclid/files/3.1.x/).
(скачал jeuclid-3.1.9-distribution.zip)

1.7.4. Скопируйте содержимое папки распакованого архива jeuclid-3.1.9/repo/*.jar  в каталог fop/lib.


1.7.5. Скопируйте образец конфигурации fop.xml из каталога etc/fop в
репозитории бекенда в каталог fop.

sudo cp /path/to/backend/repo/etc/fop/fop.xml /etc/fop.conf.d/fop/

1.7.6. Скопируйте шрифты в каталог fop/fonts.

sudo cp /path/to/fonts/\* /etc/fop.conf.d/fop/fonts/
1.7.7. Если ассеты генерируются через Symfony
  php bin/console assets:install 
  /*это должно сгенерировать *.css и *.js */
1.7.8.Создать пользователя 
  php bin/console doctrine:fixtures:load --append
  /* Это создаст user: admin passwd:adminadmin*/

## **1.9. RabbitMQ**

1.9.1. Установите RabbitMQ:

apt install rabbitmq-server

1.9.2. Включите плагин менеджмента:

rabbitmq-plugins enable rabbitmq_management

1.9.3. Добавьте пользователя с полными правами для управления:

> rabbitmqctl add_user admin 12345
>
> rabbitmqctl set_user_tags admin administrator
>
> rabbitmqctl set_permissions -p / admin ".\*" ".\*" ".\*"

## **1.10. Сrontab**

1.10.1. Добавьте следующие команды в crontab:

1.10.1.1. Каждые 5 секунд:

php bin/console messenger:consume to.backend --limit=64

1.10.1.2. Каждые 2 минуты:

> php bin/console app:sync-documents

1.10.1.3. Раз в сутки:

> php bin/console cache:pool:prune
>
> php bin/console app:create-import-documents

1.10.2. Настройте периодическую очистку логов приложения в каталоге
var/log.

# **Frontend**

## **2.1. Node.js** 

2.1.1. Установите необходимые зависимости для подключения репозиториев:

apt install -y lsb-release ca-certificates apt-transport-https
software-properties-common gnupg2

2.1.2. Добавьте ключ репозитория:

curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \|
gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg

2.1.3. Добавьте адрес репозитория:

echo "deb \[signed-by=/etc/apt/keyrings/nodesource.gpg\]
https://deb.nodesource.com/node_18.x nodistro main" \| tee
/etc/apt/sources.list.d/nodesource.list

2.1.4. Установите Node.js:

apt install nodejs

## **2.2. Создание и настройка каталога Frontend**

2.2.1. Создайте каталог сайта с правами пользователя (например,
/var/www/frontend с пользователем и группой mlt).

sudo mkdir -p /var/www/frontend

2.4.2. Изменение владельца и группы каталога:

> sudo chown -R mlt:mlt /var/www/frontend

2.4.3. Установка прав доступа:

sudo chmod -R 755 /var/www/frontend

2.4.5. Проверка прав доступа:

ls -ld /var/www/frontend

2.4.6. Загрузите в каталог исходный код фронтенда.

## **2.3. Настройка переменных окружения**

2.3.1. Скопируйте файл .env.example в .env.

cd /var/www/frontend

cp .env.example .env

2.3.2. Откройте файл .env в текстовом редакторе и измените все
переменные на свои значения.

nano .env

2.3.4. Убедитесь, что домен или IP адрес и порт, указанные в файле .env,
совпадают с настройками Nginx и переменными окружения в папке backend.
Это необходимо для корректной работы приложения и избежания ошибок
связи.

## **2.4. Зависимости**

2.4.1. Установите зависимости:

npm install

2.4.2. Выполните пост-установку:

npm run postinstall

## **2.5. Запуск приложения:**

2.5.1. Выполните команду:

npm run deploy

# **Machine Learning**

## **3.1. Пакеты и языковые модели**

3.1.1. Установка необходимых пакетов

sudo apt install poppler-utils tesseract-ocr myspell-ru python3-pip
python3-venv

2.  Загрузите языковые модели из каталога lib:

sudo cp lib/rus.traineddata /usr/share/tesseract-ocr/4.00/tessdata/

sudo cp lib/eng.traineddata /usr/share/tesseract-ocr/4.00/tessdata/

## **3.2. Python**

3.2.1. Создание виртуального окружения

1.  Создайте виртуальное окружение:

python3 -m venv /home/mlt/my_venv

3.2.2. Активация виртуального окружения

2.  Активируйте виртуальное окружение:

source /home/mlt/my_venv/bin/activate

3.2.3. Установка необходимых зависимостей

3.  Установите необходимые зависимости:

> pip install -U Flask
>
> pip install threaded
>
> pip install easyocr
>
> pip install pdf2image
>
> pip install pytesseract
>
> pip install pillow
>
> pip install translate
>
> pip install waitress
>
> pip install pyenchant
>
> pip install pandas
>
> pip install cnstd
>
> pip install pycld2
>
> pip install pika
>
> pip install retry
>
> pip install pix2tex
>
> pip install latex2mathml
>
> pip install onnxruntime
>
> pip install natsort
>
> pip install 'tensorflow==2.15.0'
>
> pip install pymorphy3
>
> pip install python-Levenshtein

## **3.3. Создание и настройка ML-каталога**

3.3.1. Создание каталога для кода

1.  Создайте каталог для кода с правами пользователя (например,
    /home/mlt/ml) и загрузите туда код.

mkdir /home/mlt/ml

3.3.2. Настройка конфигурационного файла

2.  Скопируйте файл example_settings.ini в settings.ini и заполните
    поля:

> url_server = URL до backend с префиксом
>
> cpu = Указать количество потоков
>
> url = URL rabbitMQ
>
> dir = Путь до серверного хранилища документов

3.3.3. Настройка конфигурационного файла для OCR

3.  Скопируйте файл lib/math/ocr/example_mixed.yaml в
    lib/math/ocr/mixed.yaml и замените значение строки tokenizer на
    актуальное, например:

tokenizer: /home/mlt/rst-ml/lib/math/ocr/tok_v2.json

## **3.4. PM2**

3.4.1. Установите необходимые зависимости для подключения репозиториев:

sudo apt install -y lsb-release ca-certificates apt-transport-https
software-properties-common gnupg2

3.4.2. Установите PM2 (должен быть установлен NodeJS):

npm i -g pm2

## **3.5. Запуск приложения**

3.5.1. От пользователя (например, mlt) выполните команду запуска:

pm2 -f start main.py

## **3.6. Видеодрайвер**

3.6.1. Рекомендуется использовать ускоритель (видеокарту), так как
существует большая разница в производительности в пользу ускорителя.

3.6.2. Установка драйвера на видеокарту Nvidia

sudo apt install nvidia-driver

3.6.3. После установки драйвера потребуется перезагрузка системы:

sudo reboot

## **3.7. Перезапуск сервисов**

3.7.1. Для ML (192.168.120.219): необходимо сначала активировать
окружение Python командой:

source /home/mlt/ml-venv/bin/activate

3.7.2. В случае, если приложение работает в данный момент, то его
следует предварительно выключить командой:

pm2 delete main

3.7.3. Запускать нужно из каталога приложения:

cd /home/mlt/rst-ml

3.7.4. Затем стоит запустить приложение командой:

pm2 -f start main.py

3.7.5. Логи приложения можно посмотреть командой:

pm2 log 0
