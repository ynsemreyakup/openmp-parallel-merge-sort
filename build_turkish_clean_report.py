from pathlib import Path
import csv

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.widgets.markers import makeMarker


BASE = Path("C:/tmp/parallel_merge_sort")
CSV_PATH = BASE / "results_no_threshold.csv"
PDF_PATH = BASE / "b211202019_turkce_rapor.pdf"

FONT = "ArialTR"
FONT_BOLD = "ArialTR-Bold"
pdfmetrics.registerFont(TTFont(FONT, "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont(FONT_BOLD, "C:/Windows/Fonts/arialbd.ttf"))


def load_rows():
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_styles():
    styles = getSampleStyleSheet()
    styles["Title"].fontName = FONT_BOLD
    styles["Title"].fontSize = 17
    styles.add(ParagraphStyle(
        name="BodyTR",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=10,
        leading=13.5,
        spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="HeadingTR",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=13.5,
        leading=16,
        spaceBefore=9,
        spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="CodeTR",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8.5,
        leading=10.5,
        backColor=colors.HexColor("#F3F6FA"),
        borderColor=colors.HexColor("#D4DCE8"),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=8,
    ))
    return styles


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(doc.page))
    canvas.restoreState()


def h(story, text, styles):
    story.append(Paragraph(text, styles["HeadingTR"]))


def p(story, text, styles):
    story.append(Paragraph(text, styles["BodyTR"]))


def merge_sort_diagram():
    drawing = Drawing(430, 255)
    rows = [
        (["8 3 7 1 5 2"], 25, "#EAF2FF"),
        (["8 3 7", "1 5 2"], 72, "#EAF2FF"),
        (["8", "3 7", "1", "5 2"], 119, "#FFF7ED"),
        (["3 7 8", "1 2 5"], 166, "#DCFCE7"),
        (["1 2 3 5 7 8"], 213, "#DCFCE7"),
    ]
    for boxes, y, fill in rows:
        total_width = len(boxes) * 76 + (len(boxes) - 1) * 20
        x = 215 - total_width / 2
        for label in boxes:
            drawing.add(Rect(
                x,
                255 - y,
                76,
                26,
                fillColor=colors.HexColor(fill),
                strokeColor=colors.HexColor("#9AA4B2"),
            ))
            drawing.add(String(
                x + 10,
                263 - y,
                label,
                fontName=FONT,
                fontSize=8,
                fillColor=colors.HexColor("#172033"),
            ))
            x += 96

    drawing.add(String(24, 222, "Split", fontName=FONT_BOLD, fontSize=9, fillColor=colors.HexColor("#2563EB")))
    drawing.add(String(24, 104, "Merge", fontName=FONT_BOLD, fontSize=9, fillColor=colors.HexColor("#16A34A")))
    drawing.add(Line(48, 211, 48, 138, strokeColor=colors.HexColor("#2563EB"), strokeWidth=1.3))
    drawing.add(Line(48, 118, 48, 48, strokeColor=colors.HexColor("#16A34A"), strokeWidth=1.3))
    drawing.add(String(
        58,
        8,
        "Şekil 1. Merge sort önce diziyi parçalara böler, sonra sıralı parçaları birleştirir.",
        fontName=FONT,
        fontSize=8.5,
        fillColor=colors.HexColor("#172033"),
    ))
    return drawing


def time_chart(rows):
    labels = [r["threads"] for r in rows]
    values = [float(r["median_seconds"]) for r in rows]
    d = Drawing(430, 220)
    c = VerticalBarChart()
    c.x = 45
    c.y = 35
    c.width = 340
    c.height = 145
    c.data = [values]
    c.categoryAxis.categoryNames = labels
    c.valueAxis.valueMin = 0
    c.valueAxis.valueMax = 1.6
    c.valueAxis.valueStep = 0.4
    c.bars[0].fillColor = colors.HexColor("#16A34A")
    d.add(c)
    d.add(String(142, 200, "Şekil 2. Medyan çalışma süresi", fontName=FONT, fontSize=9))
    d.add(String(180, 8, "İş parçacığı sayısı", fontName=FONT, fontSize=8))
    d.add(String(0, 96, "Saniye", fontName=FONT, fontSize=8, angle=90))
    return d


def speedup_chart(rows):
    points = [(float(r["threads"]), float(r["speedup"])) for r in rows]
    ideal = [(1.0, 1.0), (12.0, 12.0)]
    d = Drawing(430, 220)
    c = LinePlot()
    c.x = 45
    c.y = 35
    c.width = 340
    c.height = 145
    c.data = [points, ideal]
    c.xValueAxis.valueMin = 1
    c.xValueAxis.valueMax = 12
    c.xValueAxis.valueSteps = [1, 2, 4, 8, 12]
    c.yValueAxis.valueMin = 0
    c.yValueAxis.valueMax = 12
    c.yValueAxis.valueStep = 2
    c.lines[0].strokeColor = colors.HexColor("#2563EB")
    c.lines[0].symbol = makeMarker("FilledCircle")
    c.lines[1].strokeColor = colors.HexColor("#9AA4B2")
    c.lines[1].strokeDashArray = [4, 3]
    d.add(c)
    d.add(String(122, 200, "Şekil 3. Ölçülen ve ideal hızlanma", fontName=FONT, fontSize=9))
    d.add(String(180, 8, "İş parçacığı sayısı", fontName=FONT, fontSize=8))
    d.add(String(0, 100, "Hızlanma", fontName=FONT, fontSize=8, angle=90))
    return d


def main():
    rows = load_rows()
    styles = make_styles()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="OpenMP Merge Sort Türkçe Rapor",
    )

    story = []
    story.append(Paragraph("Paralel Uygulama Çalışması: OpenMP Merge Sort", styles["Title"]))
    story.append(Paragraph("OpenMP görev tabanlı paralel sıralama çalışması.", styles["BodyTR"]))

    h(story, "Özet", styles)
    p(story, "Bu çalışmada merge sort algoritması OpenMP görevleri kullanılarak paralelleştirilmiştir. İlk olarak tek iş parçacığıyla çalışan seri merge sort uygulaması referans yöntem olarak kullanılmıştır. Daha sonra aynı algoritma, sol ve sağ alt dizileri ayrı OpenMP görevleri olarak çalıştıracak şekilde paralel hale getirilmiştir. 5.000.000 rastgele tam sayı üzerinde yapılan deneyde 12 iş parçacığı ile 4.36x hızlanma elde edilmiştir.", styles)

    h(story, "1. Problem Tanımı", styles)
    p(story, "Problem, sırasız bir tam sayı dizisini küçükten büyüğe sıralamaktır. Bu problem, bilgisayar bilimlerinde çok temel bir işlemdir. Veritabanlarında kayıtların düzenlenmesi, arama işlemlerinin hızlandırılması, indeksleme, veri analizi ve birçok ön işlem adımı sıralama algoritmalarına ihtiyaç duyar.", styles)
    p(story, "Bu projede girdi olarak sabit seed ile üretilmiş 5.000.000 rastgele tam sayı kullanılmıştır. Sabit seed kullanılması, her çalıştırmada aynı veri kümesinin üretilmesini sağlar. Böylece seri ve paralel sürümlerin aynı girdi üzerinde karşılaştırılması mümkün olur.", styles)

    h(story, "2. Merge Sort Algoritması", styles)
    p(story, "Merge sort, böl ve yönet yaklaşımıyla çalışan bir sıralama algoritmasıdır. Algoritma önce diziyi iki parçaya böler. Sonra sol parça ve sağ parça ayrı ayrı sıralanır. Son aşamada iki sıralı parça birleştirilerek daha büyük sıralı bir parça elde edilir. Bu işlem recursive olarak devam eder ve dizi tek elemana kadar bölünür. Tek elemanlı bir dizi zaten sıralı kabul edilir.", styles)
    story.append(merge_sort_diagram())
    story.append(Paragraph(
        "merge_sort(array):<br/>"
        "&nbsp;&nbsp;if array size is 1, return<br/>"
        "&nbsp;&nbsp;split array into left and right<br/>"
        "&nbsp;&nbsp;merge_sort(left)<br/>"
        "&nbsp;&nbsp;merge_sort(right)<br/>"
        "&nbsp;&nbsp;merge(left, right)",
        styles["CodeTR"],
    ))
    p(story, "Merge adımı iki sıralı alt diziyi tek bir sıralı diziye dönüştürür. Örneğin [3, 7, 8] ve [1, 2, 5] parçaları birleştirildiğinde [1, 2, 3, 5, 7, 8] sonucu elde edilir. Bu nedenle merge sort'un doğruluğu, bölme işleminden sonra alt parçaların doğru sıralanmasına ve merge adımının doğru çalışmasına bağlıdır.", styles)

    h(story, "3. Seri Referans Uygulama", styles)
    p(story, "Seri sürüm, algoritmanın tek iş parçacığıyla çalışan referans halidir. Bu sürümde sol alt dizi sıralanır, ardından sağ alt dizi sıralanır ve daha sonra iki parça birleştirilir. Seri sürüm iki amaçla kullanılmıştır. Birincisi, paralel sürümün doğru sonuç üretip üretmediğini karşılaştırmak için referans sağlamaktır. İkincisi, hızlanma değerini hesaplamak için başlangıç çalışma süresini vermektir.", styles)

    h(story, "4. OpenMP ile Paralelleştirme", styles)
    p(story, "Merge sort paralelleştirmeye uygundur çünkü sol ve sağ yarılar birleştirme adımından önce birbirinden bağımsızdır. Sol yarının sıralanması sağ yarının sonucuna bağlı değildir; sağ yarının sıralanması da sol yarının sonucuna bağlı değildir. Bu nedenle bu iki işlem aynı anda farklı iş parçacıkları tarafından yürütülebilir.", styles)
    p(story, "OpenMP görev modeli bu yapı için uygundur. Kodda sol yarıyı sıralamak için bir OpenMP görevi, sağ yarıyı sıralamak için ikinci bir OpenMP görevi oluşturulur. Üst görev, taskwait komutu ile iki alt görevin tamamlanmasını bekler. İki taraf da sıralandıktan sonra merge işlemi yapılır.", styles)
    story.append(Paragraph(
        "#pragma omp task<br/>"
        "parallel_merge_sort(left)<br/><br/>"
        "#pragma omp task<br/>"
        "parallel_merge_sort(right)<br/><br/>"
        "#pragma omp taskwait<br/>"
        "merge(left, right)",
        styles["CodeTR"],
    ))
    p(story, "taskwait komutu doğruluk açısından önemlidir. Çünkü merge işlemi yapılmadan önce sol ve sağ parçaların sıralanmış olması gerekir. Eğer merge işlemi alt görevler bitmeden başlarsa, henüz sıralanmamış veriler birleştirilebilir ve sonuç hatalı olur.", styles)

    h(story, "5. Doğruluk Kontrolü", styles)
    p(story, "Doğruluk iki yöntemle kontrol edilmiştir. İlk olarak is_sorted testi kullanılmıştır. Bu test, sonuç dizisinin gerçekten küçükten büyüğe sıralı olup olmadığını kontrol eder. İkinci olarak checksum değeri hesaplanmıştır. Checksum, dizideki tüm elemanların toplamıdır. Sıralama işlemi elemanların yerini değiştirir fakat elemanların değerlerini değiştirmemelidir.", styles)
    p(story, "Tüm çalıştırmalarda sorted = true sonucu elde edilmiştir. Ayrıca seri ve paralel tüm koşullarda checksum değeri 2.499.530.084.831.184 olarak aynı çıkmıştır. Bu sonuç, paralel uygulamanın hem sıralı hem de aynı elemanları içeren doğru bir çıktı ürettiğini göstermektedir.", styles)

    h(story, "6. Deney Düzeneği", styles)
    setup = [
        ["Öğe", "Değer"],
        ["Dil", "C++"],
        ["Paralel model", "OpenMP görevleri"],
        ["Girdi", "5.000.000 rastgele tam sayı"],
        ["İş parçacığı sayıları", "1, 2, 4, 8, 12"],
        ["Tekrar", "Her konfigürasyon için 5 tekrar"],
        ["Raporlanan ölçüm", "Medyan çalışma süresi"],
        ["Derleme", "g++ -O3 -fopenmp -std=c++17"],
    ]
    table = Table(setup, colWidths=[4.4 * cm, 9.8 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2FF")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9AA4B2")),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, 1), (0, -1), FONT_BOLD),
        ("FONTNAME", (1, 1), (1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ]))
    story.append(table)
    p(story, "Her konfigürasyon beş kez çalıştırılmış ve medyan süre raporlanmıştır. Medyan kullanılması, arka plan işlemleri veya anlık sistem dalgalanmaları nedeniyle oluşabilecek uç değerlerin etkisini azaltır. Zaman ölçümüne girdi üretimi ve dosya çıktısı dahil edilmemiştir; sadece sıralama işlemi ölçülmüştür.", styles)

    h(story, "7. Performans Ölçütleri", styles)
    p(story, "Çalışma süresi, sıralama işleminin kaç saniye sürdüğünü gösterir. Hızlanma, seri çalışma süresinin paralel çalışma süresine bölünmesiyle hesaplanır. Verimlilik ise hızlanma değerinin kullanılan iş parçacığı sayısına bölünmesidir.", styles)
    story.append(Paragraph(
        "speedup = sequential_time / parallel_time<br/>"
        "efficiency = speedup / thread_count",
        styles["CodeTR"],
    ))

    h(story, "8. Performans Sonuçları", styles)
    result = [["Mod", "İş parçacığı", "Süre (s)", "Hızlanma", "Verimlilik", "Sorted", "Checksum"]]
    for r in rows:
        result.append([
            "seri" if r["mode"] == "sequential" else "openmp",
            r["threads"],
            f'{float(r["median_seconds"]):.3f}',
            f'{float(r["speedup"]):.3f}',
            f'{float(r["efficiency"]):.3f}',
            r["sorted"],
            r["checksum"],
        ])
    table = Table(result, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2FF")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#777777")),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("ALIGN", (1, 1), (4, -1), "RIGHT"),
        ("ALIGN", (6, 1), (6, -1), "RIGHT"),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2 * cm))
    story.append(KeepTogether([time_chart(rows), Spacer(1, 0.1 * cm), speedup_chart(rows)]))

    h(story, "9. Sonuçların Yorumu", styles)
    p(story, "Seri çalışma süresi 1.498 saniyedir. 12 iş parçacığı ile çalışma süresi 0.343 saniyeye düşmüştür. Bu sonuç 4.36x hızlanma anlamına gelir. Paralel sürüm, seri sürüme göre belirgin şekilde daha hızlıdır.", styles)
    p(story, "Buna rağmen hızlanma doğrusal değildir. 12 iş parçacığı kullanıldığında teorik olarak 12x hızlanma beklenebilir; fakat pratikte bu değere ulaşılamaz. Bunun başlıca sebepleri merge işleminin yoğun bellek hareketi yapması, OpenMP görev oluşturma maliyeti ve taskwait senkronizasyonudur. Özellikle merge adımı sırasında veriler ana dizi ile geçici buffer arasında taşındığı için bellek erişimi performansı sınırlar.", styles)

    h(story, "10. Sonuç", styles)
    p(story, "Bu çalışma, merge sort algoritmasının OpenMP görevleri ile paralelleştirilebildiğini göstermektedir. Sol ve sağ alt dizilerin bağımsız olması, algoritmanın doğal bir paralel yapıya sahip olmasını sağlar. Doğruluk is_sorted ve checksum ile doğrulanmıştır. Performans deneyinde 5.000.000 tam sayı üzerinde 12 iş parçacığı ile 4.36x hızlanma elde edilmiştir.", styles)

    story.append(PageBreak())
    h(story, "Ek: Kullanılan Komutlar", styles)
    story.append(Paragraph(
        "Derleme:<br/>"
        "g++ -O3 -fopenmp -std=c++17 parallel_merge_sort_simple.cpp -o parallel_merge_sort_simple.exe<br/><br/>"
        "Deney:<br/>"
        "parallel_merge_sort_simple.exe 5000000 5<br/><br/>"
        "Hızlı demo:<br/>"
        "parallel_merge_sort_simple.exe 200000 3",
        styles["CodeTR"],
    ))

    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    print(PDF_PATH)


if __name__ == "__main__":
    main()
