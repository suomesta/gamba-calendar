import calendar
import html
import json
import shutil
import urllib.parse
from datetime import UTC, datetime, timedelta
from pathlib import Path

OUTPUT_DIR = Path("output")
ICON_DIR = Path("icons")
ICS_DIR = OUTPUT_DIR / "ics"

OUTPUT_DIR.mkdir(exist_ok=True)
ICS_DIR.mkdir(exist_ok=True)


def parse_dt(v):
    return datetime.fromisoformat(v)


def utc_format(dt):
    return dt.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def google_link(match):

    start = utc_format(parse_dt(match['start']))
    end = utc_format(parse_dt(match['start']) + timedelta(hours=2))
    details = match["competition"]

    params = {
        "action": "TEMPLATE",
        "text": match["title"],
        "dates": f"{start}/{end}",
        "location": match["location"],
        "details": details
    }

    return \
        "https://calendar.google.com/calendar/render?" + \
        urllib.parse.urlencode(params)


def create_ics(match):

    start = utc_format(parse_dt(match['start']))
    end = utc_format(parse_dt(match['start']) + timedelta(hours=2))
    details = match["competition"]

    content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Gamba Calendar//JP
BEGIN:VEVENT
UID:{match['id']}@gamba-calendar
DTSTAMP:{utc_format(datetime.now(UTC))}
DTSTART:{start}
DTEND:{end}
SUMMARY:{match['title']}
LOCATION:{match['location']}
DESCRIPTION:{details}
END:VEVENT
END:VCALENDAR
"""

    filename = ICS_DIR / f"{match['id']}.ics"

    with open(
        filename,
        "w",
        encoding="utf-8",
        newline="\r\n"
    ) as f:
        f.write(content)


def month_key(match):
    dt = parse_dt(match["start"])
    return dt.year, dt.month


def render_match(match):
    opponent = (match["title"].replace("ガンバ大阪 vs ", "")
                              .replace(" vs ガンバ大阪", ""))
    opponent = html.escape(opponent)
    css = "home" if "吹田" in match["location"] else "away"
    competition = html.escape(match["competition"])
    youtube = match.get("youtube", {})
    if isinstance(youtube, str):
        youtube = {"YouTube": youtube} if youtube else {}

    payload = html.escape(json.dumps({
        "title": match["title"],
        "competition": match["competition"],
        "location": match["location"],
        "start": match["start"],
        "result": match["result"],
        "youtube": youtube,
        "google": google_link(match),
        "ics": f"ics/{match['id']}.ics"
    }))

    result = ""
    if match["result"]:
        result = ", " + match["result"]
    return f"""
<div class="match {css}"
onclick='showMatch({payload})'>
<strong>{opponent}</strong><br>
{parse_dt(match["start"]).strftime("%H:%M")}{result}
<span class="match-info">{competition}</span>
</div>
"""


def create_html(matches):

    grouped = {}

    for m in matches:

        key = month_key(m)

        grouped.setdefault(key, []).append(m)

    sorted_months = sorted(grouped.items())

    html_text = r"""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="icons/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="icons/favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="icons/favicon-192.png">
<link rel="icon" type="image/png" sizes="512x512" href="icons/favicon-512.png">
<link rel="apple-touch-icon" href="icons/favicon-192.png">

<title>ガンバ大阪カレンダー</title>

<style>

body{
    font-family:sans-serif;
    margin:20px;
}

.nav{
    display:flex;
    gap:10px;
    justify-content:center;
    align-items:center;
    margin-bottom:20px;
}

.month{
    display:none;
}

.month.active{
    display:block;
}

table{
    width:100%;
    border-collapse:collapse;
}

th,td{
    border:1px solid #ccc;
    width:14%;
    vertical-align:top;
    padding:4px;
}

th.sun{
    color:red;
}

th.sat{
    color:blue;
}

.day{
    font-weight:bold;
}

.today{
    background:#fff5a8;
}

.match{
    margin-top:4px;
    border-radius:4px;
    padding:4px;
    font-size:12px;
    cursor:pointer;
}

.match-info{
    display:block;
    margin-top:3px;
    font-size:10px;
}

.mobile-date{
    display:none;
}

.mobile-columns{
    display:none;
}

.home{
    background:#004e98;
    color:white;
}

.away{
    background:#333;
    color:white;
}

.legend{
    margin-bottom:10px;
}

.legend-item{
    display:inline-block;
    padding:4px 10px;
    border-radius:4px;
    font-size:12px;
    color:white;
    margin-right:10px;
}

.legend-home{
    background:#004e98;
}

.legend-away{
    background:#333;
}

.match a{
    color:inherit;
}

.modal{
    display:none;
    position:fixed;
    inset:0;
    background:rgba(0,0,0,0.6);
}

.modal-content{
    background:white;
    max-width:600px;
    margin:5% auto;
    padding:20px;
}

.close-btn{
    float:right;
}

@media(max-width:768px){

    body{
        margin:12px;
    }

    .nav{
        gap:8px;
        margin-bottom:14px;
    }

    .nav button{
        min-width:44px;
        min-height:44px;
        font-size:16px;
    }

    #month-title{
        font-size:18px;
        font-weight:bold;
    }

    .month table{
        display:none;
    }

    .mobile-columns{
        display:block;
    }

    .mobile-week{
        display:grid;
        grid-template-columns:repeat(3, minmax(0, 1fr));
        gap:6px;
    }

    .mobile-week{
        margin-top:6px;
    }

    .mobile-week-cell{
        min-width:0;
        min-height:36px;
        padding:3px;
        border:1px solid #ddd;
        border-radius:6px;
        background:#fff;
    }

    .mobile-match-day{
        margin-bottom:4px;
        padding:4px 2px;
        border-radius:4px;
    }

    .mobile-match-day.today{
        background:#fff5a8;
    }

    .mobile-date{
        display:block;
        margin-bottom:4px;
        text-align:center;
        font-size:11px;
        font-weight:bold;
        white-space:nowrap;
    }

    .mobile-date .sunday{
        color:red;
    }

    .mobile-date .saturday{
        color:blue;
    }

    .mobile-match-day .match{
        margin-top:4px;
        padding:5px 4px;
        font-size:11px;
        line-height:1.3;
    }

    .match-info{
        display:block;
        margin-top:2px;
        font-size:10px;
        opacity:.9;
    }

    .modal-content{
        box-sizing:border-box;
        width:calc(100% - 24px);
        max-height:calc(100% - 32px);
        margin:16px auto;
        padding:18px;
        overflow-y:auto;
    }

    .legend-item{
        padding:8px 12px;
        font-size:14px;
    }

}

</style>
</head>
<body>

<div class="nav">
<button onclick="prevMonth()">◀</button>
<span id="month-title"></span>
<button onclick="nextMonth()">▶</button>
<button onclick="goCurrentMonth()">今月</button>
</div>

"""

    cal = calendar.Calendar(firstweekday=6)

    for idx, ((year, month), month_matches) in enumerate(sorted_months):

        match_map = {}
        weekday_names = ("月", "火", "水", "木", "金", "土", "日")

        for m in month_matches:

            day = parse_dt(m["start"]).day

            match_map.setdefault(day, []).append(m)

        html_text += f"""
<div class="month" data-index="{idx}" data-title="{year}年{month}月"
 data-year="{year}" data-month="{month}">

<table>
<tr>
<th class="sun">日</th>
<th>月</th>
<th>火</th>
<th>水</th>
<th>木</th>
<th>金</th>
<th class="sat">土</th>
</tr>
"""

        for week in cal.monthdayscalendar(year, month):

            html_text += "<tr>"

            for day in week:

                if day == 0:
                    html_text += "<td></td>"
                    continue

                date_value = f"{year:04d}-{month:02d}-{day:02d}"

                day_matches = match_map.get(day, [])
                cell_classes = []
                if day_matches:
                    cell_classes.append("has-matches")
                cell_class = " ".join(cell_classes)

                html_text += \
                    f'<td class="{cell_class}" data-date="{date_value}">' \
                    f'<div class="day">{day}</div>'

                for m in day_matches:
                    html_text += render_match(m)

                html_text += "</td>"

            html_text += "</tr>"

        html_text += "</table>"

        html_text += '<div class="mobile-columns">'

        for week in cal.monthdayscalendar(year, month):
            week_cells = [[], [], []]
            for weekday_index, day in enumerate(week):
                if day == 0 or day not in match_map:
                    continue

                column_index = 0 if weekday_index == 0 else (
                    1 if weekday_index <= 4 else 2
                )
                weekday = calendar.weekday(year, month, day)
                weekday_class = "saturday" if weekday == 5 else (
                    "sunday" if weekday == 6 else ""
                )
                date_label = (
                    f'<div class="mobile-date">{month:02d}月{day:02d}日'
                    f'(<span class="{weekday_class}">'
                    f'{weekday_names[weekday]}</span>)</div>'
                )
                match_cards = "".join(
                    render_match(match) for match in match_map[day]
                )
                week_cells[column_index].append(
                    f'<div class="mobile-match-day" data-date="{year:04d}-'
                    f'{month:02d}-{day:02d}">{date_label}{match_cards}</div>'
                )

            html_text += '<div class="mobile-week">'
            for cell_days in week_cells:
                html_text += '<div class="mobile-week-cell">'
                html_text += "".join(cell_days)
                html_text += "</div>"
            html_text += "</div>"

        html_text += "</div></div>"

    html_text += """
<div id="modal" class="modal">

<div class="modal-content">

<button class="close-btn"
onclick="closeModal()">×</button>

<div id="modal-body"></div>

</div>

</div>

<div class="legend">
<span class="legend-item legend-home">
ホーム
</span>
<span class="legend-item legend-away">
アウェー
</span>
</div>

<script>

let currentMonth=0;

const months =
 document.querySelectorAll(".month");

const title =
 document.getElementById("month-title");

function updateView(){
    months.forEach(
      m=>m.classList.remove("active"));

    months[currentMonth]
      .classList.add("active");

    title.textContent =
        months[currentMonth].dataset.title;
}

function getTokyoDate(){
    return Object.fromEntries(
        new Intl.DateTimeFormat("en", {
            timeZone: "Asia/Tokyo",
            year: "numeric",
            month: "2-digit",
            day: "2-digit"
        }).formatToParts(new Date())
          .map(({type, value}) => [type, value])
    );
}

function getCurrentMonthIndex(){
    const today = getTokyoDate();

    return Array.from(months).findIndex(
        month => Number(month.dataset.year) === Number(today.year)
          && Number(month.dataset.month) === Number(today.month)
    );
}

function updateToday(){
    const today = getTokyoDate();
    const dateValue = `${today.year}-${today.month}-${today.day}`;

    document.querySelectorAll(".month [data-date]").forEach(
        cell => cell.classList.toggle(
            "today",
            cell.dataset.date === dateValue
        )
    );
}

function prevMonth(){
    if(currentMonth>0){
        currentMonth--;
        updateView();
    }
}

function nextMonth(){
    if(currentMonth<months.length-1){
        currentMonth++;
        updateView();
    }
}

document.addEventListener("keydown", event => {
    if (!window.matchMedia("(min-width: 769px)").matches
        || event.altKey || event.ctrlKey || event.metaKey
        || event.target instanceof Element
            && event.target.closest("input, textarea, select, [contenteditable='true']")
        || document.getElementById("modal").style.display === "block") {
        return;
    }

    if (event.key === "ArrowLeft") {
        event.preventDefault();
        prevMonth();
    } else if (event.key === "ArrowRight") {
        event.preventDefault();
        nextMonth();
    }
});

let wheelNavigationLocked = false;
let wheelNavigationTimeout;

document.addEventListener("wheel", event => {
    if (!window.matchMedia("(min-width: 769px)").matches
        || !event.deltaY
        || !(event.target instanceof Element)
        || !event.target.closest(".month.active")) {
        return;
    }

    event.preventDefault();

    if (!wheelNavigationLocked) {
        wheelNavigationLocked = true;
        if (event.deltaY > 0) {
            nextMonth();
        } else {
            prevMonth();
        }
    }

    clearTimeout(wheelNavigationTimeout);
    wheelNavigationTimeout = setTimeout(() => {
        wheelNavigationLocked = false;
    }, 200);
}, {passive: false});

let touchStartX = null;
let touchStartY = null;

document.addEventListener("touchstart", event => {
    if (event.touches.length !== 1
        || !(event.target instanceof Element)
        || !event.target.closest(".month.active")) {
        touchStartX = null;
        touchStartY = null;
        return;
    }

    touchStartX = event.touches[0].clientX;
    touchStartY = event.touches[0].clientY;
}, {passive: true});

document.addEventListener("touchend", event => {
    if (touchStartX === null || touchStartY === null
        || event.changedTouches.length !== 1) {
        touchStartX = null;
        touchStartY = null;
        return;
    }

    const deltaX = event.changedTouches[0].clientX - touchStartX;
    const deltaY = event.changedTouches[0].clientY - touchStartY;
    touchStartX = null;
    touchStartY = null;

    if (Math.abs(deltaX) < 50 || Math.abs(deltaX) <= Math.abs(deltaY)) {
        return;
    }

    event.preventDefault();

    if (deltaX > 0) {
        prevMonth();
    } else {
        nextMonth();
    }
}, {passive: false});

function goCurrentMonth(){
    const index = getCurrentMonthIndex();
    currentMonth = index < 0 ? 0 : index;
    updateView();
}

function closeModal(){
 document.getElementById("modal")
 .style.display="none";
}

document.getElementById("modal").addEventListener("click", event => {
    if (event.target === event.currentTarget) {
        closeModal();
    }
});

function shareEvent(title,url){
    if(navigator.share){
       navigator.share({
          title:title,
          url:url
       });
    }
}

function formatJST(isoString){

    const d = new Date(isoString);

    return d.toLocaleString(
        "ja-JP",
        {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            weekday: "short",
            hour: "2-digit",
            minute: "2-digit",
            timeZone: "Asia/Tokyo"
        }
    );
}

function showMatch(m){

 document.getElementById(
  "modal-body").innerHTML=`

<h2>${m.title}</h2>

<p><b>大会</b><br>${m.competition}</p>

<p><b>日時</b><br>${formatJST(m.start)}～</p>

<p><b>会場</b><br>${m.location}</p>

<div id="youtube-links"></div>

${m.result ? `
<p><b>結果</b><br>${m.result}</p>
` : ""}

<p>
<b>カレンダー</b><br>
<a target="_blank" href="${m.google}">Google</a>　　<a href="${m.ics}">ICS</a>
</p>
`;

 const youtubeContainer = document.getElementById("youtube-links");
 const youtubeLinks = Object.entries(m.youtube);

 if (youtubeLinks.length) {
     const heading = document.createElement("b");
     heading.textContent = "動画";
     youtubeContainer.append(heading, document.createElement("br"));

     youtubeLinks.forEach(([label, url], index) => {
         if (index > 0) {
             youtubeContainer.append("　　");
         }

         const link = document.createElement("a");
         link.href = url;
         link.target = "_blank";
         link.rel = "noopener noreferrer";
         link.textContent = label;
         youtubeContainer.append(link);
     });
 } else {
     youtubeContainer.remove();
 }

 document.getElementById("modal")
 .style.display="block";
}

goCurrentMonth();
updateToday();
setInterval(updateToday, 60 * 1000);

</script>

</body>
</html>
"""

    with open(
        OUTPUT_DIR / "index.html",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(html_text)


def main():

    with open(
        "matches.json",
        encoding="utf-8"
    ) as f:
        matches = json.load(f)

    for m in matches:
        create_ics(m)

    create_html(matches)
    shutil.copytree(ICON_DIR, OUTPUT_DIR / "icons", dirs_exist_ok=True)

    print("generated")


if __name__ == "__main__":
    main()
