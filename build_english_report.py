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
    KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.widgets.markers import makeMarker


BASE = Path("C:/tmp/parallel_merge_sort")
CSV_PATH = BASE / "results_no_threshold.csv"
PDF_PATH = BASE / "b211202019_english_report.pdf"
RESULT_FILES = {
    "5M Threshold": BASE / "results_5m_threshold.csv",
    "5M No Threshold": BASE / "results_5m_no_threshold.csv",
    "50M Threshold": BASE / "results_50m_threshold.csv",
    "50M No Threshold": BASE / "results_50m_no_threshold.csv",
}

FONT = "ArialEN"
FONT_BOLD = "ArialEN-Bold"
pdfmetrics.registerFont(TTFont(FONT, "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont(FONT_BOLD, "C:/Windows/Fonts/arialbd.ttf"))


def load_rows():
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_result_file(path):
    path = Path(path)
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            with path.open(newline="", encoding=encoding) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def load_all_results():
    return {name: load_result_file(path) for name, path in RESULT_FILES.items()}


def make_styles():
    styles = getSampleStyleSheet()
    styles["Title"].fontName = FONT_BOLD
    styles["Title"].fontSize = 17
    styles.add(ParagraphStyle(
        name="BodyEN",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=10,
        leading=13.5,
        spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="HeadingEN",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=13.5,
        leading=16,
        spaceBefore=9,
        spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="CodeEN",
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
    story.append(Paragraph(text, styles["HeadingEN"]))


def p(story, text, styles):
    story.append(Paragraph(text, styles["BodyEN"]))


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
        "Figure 1. Merge sort first splits the array, then merges the sorted parts.",
        fontName=FONT,
        fontSize=8.5,
        fillColor=colors.HexColor("#172033"),
    ))
    return drawing


def build_combined_rows(results, size_label):
    threshold_rows = results[f"{size_label} Threshold"]
    no_threshold_rows = results[f"{size_label} No Threshold"]
    combined = []
    for version, rows in [("Threshold", threshold_rows), ("No Threshold", no_threshold_rows)]:
        for r in rows:
            combined.append({
                "version": version,
                "threads": r["threads"],
                "time": float(r["median_seconds"]),
                "speedup": float(r["speedup"]),
                "efficiency": float(r["efficiency"]),
                "checksum": r["checksum"],
                "sorted": r["sorted"],
            })
    return combined


def make_comparison_table(results, size_label):
    table_data = [["Version", "Threads", "Time (s)", "Speedup", "Efficiency", "Sorted", "Checksum"]]
    for r in build_combined_rows(results, size_label):
        table_data.append([
            r["version"],
            r["threads"],
            f'{r["time"]:.3f}',
            f'{r["speedup"]:.3f}',
            f'{r["efficiency"]:.3f}',
            r["sorted"],
            r["checksum"],
        ])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF2FF")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#777777")),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 7.3),
        ("ALIGN", (1, 1), (4, -1), "RIGHT"),
        ("ALIGN", (6, 1), (6, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    return table


def metric_points(rows, metric):
    return [(float(r["threads"]), float(r[metric])) for r in rows]


def thread_line_chart(results, size_label, metric, title, y_label, y_max, y_step, figure_no):
    threshold_points = metric_points(results[f"{size_label} Threshold"], metric)
    no_threshold_points = metric_points(results[f"{size_label} No Threshold"], metric)
    d = Drawing(430, 220)
    c = LinePlot()
    c.x = 45
    c.y = 35
    c.width = 340
    c.height = 145
    c.data = [threshold_points, no_threshold_points]
    c.xValueAxis.valueMin = 1
    c.xValueAxis.valueMax = 12
    c.xValueAxis.valueSteps = [1, 2, 4, 8, 12]
    c.yValueAxis.valueMin = 0
    c.yValueAxis.valueMax = y_max
    c.yValueAxis.valueStep = y_step
    c.lines[0].strokeColor = colors.HexColor("#2563EB")
    c.lines[0].symbol = makeMarker("FilledCircle")
    c.lines[1].strokeColor = colors.HexColor("#F97316")
    c.lines[1].symbol = makeMarker("FilledSquare")
    d.add(c)
    d.add(String(78, 200, f"Figure {figure_no}. {title} ({size_label})", fontName=FONT, fontSize=9))
    d.add(String(185, 8, "Number of threads", fontName=FONT, fontSize=8))
    d.add(String(0, 96, y_label, fontName=FONT, fontSize=8, angle=90))
    d.add(String(295, 170, "Threshold", fontName=FONT, fontSize=8, fillColor=colors.HexColor("#2563EB")))
    d.add(String(295, 156, "No Threshold", fontName=FONT, fontSize=8, fillColor=colors.HexColor("#F97316")))
    return d


def thread_time_chart(results, size_label, figure_no):
    y_max = 0.7 if size_label == "5M" else 7.5
    y_step = 0.1 if size_label == "5M" else 1.5
    return thread_line_chart(
        results,
        size_label,
        "median_seconds",
        "Execution time vs. thread count",
        "Seconds",
        y_max,
        y_step,
        figure_no,
    )


def thread_speedup_chart(results, size_label, figure_no):
    return thread_line_chart(
        results,
        size_label,
        "speedup",
        "Speedup vs. thread count",
        "Speedup",
        5,
        1,
        figure_no,
    )


def thread_efficiency_chart(results, size_label, figure_no):
    return thread_line_chart(
        results,
        size_label,
        "efficiency",
        "Efficiency vs. thread count",
        "Efficiency",
        1,
        0.2,
        figure_no,
    )


def main():
    results = load_all_results()
    styles = make_styles()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title="OpenMP Merge Sort English Report",
    )

    story = []
    story.append(Paragraph("Parallel Implementation Study: OpenMP Merge Sort", styles["Title"]))
    story.append(Paragraph("OpenMP task-based parallel sorting study.", styles["BodyEN"]))

    h(story, "Abstract", styles)
    p(story, "In this study, the merge sort algorithm is parallelized using OpenMP tasks. First, a sequential merge sort implementation is used as the reference method. Then, the same algorithm is parallelized by executing the left and right subarrays as separate OpenMP tasks. Two implementation variants are evaluated: a threshold-based version and a no-threshold version. Experiments are performed with 5,000,000 and 50,000,000 random integers.", styles)

    h(story, "1. Problem Definition", styles)
    p(story, "The problem is to sort an unordered integer array in nondecreasing order. Sorting is a fundamental operation in computer science. Databases, search systems, indexing, data analysis, and many preprocessing pipelines require sorting algorithms.", styles)
    p(story, "In this project, the inputs consist of 5,000,000 and 50,000,000 random integers generated with a fixed seed. Using a fixed seed ensures that the same data set is generated in every run. Therefore, the sequential, threshold-based, and no-threshold versions can be compared fairly on the same input.", styles)

    h(story, "2. Merge Sort Algorithm", styles)
    p(story, "Merge sort is a sorting algorithm based on the divide-and-conquer approach. The algorithm first splits the array into two parts. Then, the left part and the right part are sorted separately. Finally, the two sorted parts are merged to obtain a larger sorted part. This process continues recursively until the array is split into single elements. A single-element array is already considered sorted.", styles)
    story.append(merge_sort_diagram())
    story.append(Paragraph(
        "merge_sort(array):<br/>"
        "&nbsp;&nbsp;if array size is 1, return<br/>"
        "&nbsp;&nbsp;split array into left and right<br/>"
        "&nbsp;&nbsp;merge_sort(left)<br/>"
        "&nbsp;&nbsp;merge_sort(right)<br/>"
        "&nbsp;&nbsp;merge(left, right)",
        styles["CodeEN"],
    ))
    p(story, "The merge step converts two sorted subarrays into one sorted array. For example, when the parts [3, 7, 8] and [1, 2, 5] are merged, the result is [1, 2, 3, 5, 7, 8]. Therefore, the correctness of merge sort depends on correctly sorting the subparts and correctly implementing the merge step.", styles)

    h(story, "3. Sequential Reference Implementation", styles)
    p(story, "The sequential version is the single-threaded reference form of the algorithm. In this version, the left subarray is sorted, then the right subarray is sorted, and then the two parts are merged. The sequential version is used for two purposes. First, it provides a reference for checking whether the parallel version produces the correct result. Second, it provides the baseline execution time used to calculate speedup.", styles)

    h(story, "4. Parallelization with OpenMP", styles)
    p(story, "Merge sort is suitable for parallelization because the left and right halves are independent before the merge step. Sorting the left half does not depend on the result of the right half, and sorting the right half does not depend on the result of the left half. Therefore, these two operations can be executed at the same time by different threads.", styles)
    p(story, "The OpenMP task model fits this structure. In the code, one OpenMP task is created to sort the left half, and a second OpenMP task is created to sort the right half. The parent task waits for both child tasks to finish using the taskwait directive. After both sides are sorted, the merge operation is performed.", styles)
    story.append(Paragraph(
        "#pragma omp task<br/>"
        "parallel_merge_sort(left)<br/><br/>"
        "#pragma omp task<br/>"
        "parallel_merge_sort(right)<br/><br/>"
        "#pragma omp taskwait<br/>"
        "merge(left, right)",
        styles["CodeEN"],
    ))
    p(story, "The taskwait directive is important for correctness. Before the merge operation can be performed, the left and right parts must already be sorted. If the merge step starts before the child tasks finish, unsorted data may be merged and the final result may be incorrect.", styles)

    h(story, "5. Threshold and No-Threshold Variants", styles)
    p(story, "Two variants are compared. The threshold-based version avoids creating OpenMP tasks for very small subarrays and uses direct sorting for small ranges. This reduces task management overhead and excessive recursive work. The no-threshold version follows the basic recursive structure more directly and continues splitting down to single elements while only limiting the recursion depth used for task creation.", styles)
    p(story, "The purpose of comparing these two variants is to observe whether the threshold optimization improves actual execution time for different input sizes. Since speedup is calculated relative to each variant's own sequential baseline, execution time should also be considered when interpreting the results.", styles)

    h(story, "6. Correctness Verification", styles)
    p(story, "Correctness is verified in two ways. First, the is_sorted test is used. This test checks whether the final output array is actually sorted in nondecreasing order. Second, the checksum value is calculated. The checksum is the sum of all elements in the array. Sorting changes the positions of the elements, but it must not change their values.", styles)
    p(story, "In all runs, the result of the sorted check is true. In addition, the checksum value is the same for all sequential and parallel configurations: 2,499,530,084,831,184. This result shows that the parallel implementation produces a sorted output containing the same elements as the sequential version.", styles)

    h(story, "7. Experimental Setup", styles)
    setup = [
        ["Item", "Value"],
        ["Language", "C++"],
        ["Parallel model", "OpenMP tasks"],
        ["Inputs", "5,000,000 and 50,000,000 random integers"],
        ["Versions", "Threshold and No Threshold"],
        ["Thread counts", "1, 2, 4, 8, 12"],
        ["Repeats", "5 repetitions for each configuration"],
        ["Reported metric", "Median execution time"],
        ["Compilation", "g++ -O3 -fopenmp -std=c++17"],
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
    p(story, "Each configuration is executed five times, and the median time is reported. Using the median reduces the effect of outliers that may occur due to background processes or temporary system noise. Input generation and file output are not included in the timing; only the sorting operation is measured.", styles)

    h(story, "8. Performance Metrics", styles)
    p(story, "Execution time shows how many seconds the sorting operation takes. Speedup is calculated by dividing the sequential execution time by the parallel execution time. Efficiency is calculated by dividing the speedup value by the number of threads used.", styles)
    story.append(Paragraph(
        "speedup = sequential_time / parallel_time<br/>"
        "efficiency = speedup / thread_count",
        styles["CodeEN"],
    ))

    h(story, "9. Performance Results", styles)
    p(story, "Table 1 reports the results for 5,000,000 integers. Table 2 reports the results for 50,000,000 integers. In both tables, the checksum remains identical between the threshold and no-threshold versions for the same input size, and all sorted checks are true.", styles)
    story.append(Paragraph("Table 1. Threshold and no-threshold results for 5,000,000 integers.", styles["BodyEN"]))
    story.append(make_comparison_table(results, "5M"))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph("Table 2. Threshold and no-threshold results for 50,000,000 integers.", styles["BodyEN"]))
    story.append(make_comparison_table(results, "50M"))
    story.append(Spacer(1, 0.2 * cm))
    p(story, "The following figures plot the 50,000,000 element experiment against thread count. They show how execution time, speedup, and efficiency change as more OpenMP threads are used.", styles)
    story.append(KeepTogether([
        thread_time_chart(results, "50M", 2),
        Spacer(1, 0.1 * cm),
        thread_speedup_chart(results, "50M", 3),
    ]))
    story.append(thread_efficiency_chart(results, "50M", 4))

    h(story, "10. Discussion", styles)
    p(story, "For 5,000,000 integers, the threshold version is faster in actual execution time at 12 threads: 0.134 seconds compared with 0.150 seconds for the no-threshold version. For 50,000,000 integers, the threshold version is also faster at 12 threads: 1.618 seconds compared with 1.699 seconds. This indicates that the threshold optimization reduces overhead and improves runtime.", styles)
    p(story, "The no-threshold version sometimes shows a slightly higher speedup because speedup is calculated relative to each version's own sequential baseline. If a version has a slower sequential baseline, its speedup can appear higher even when its actual parallel runtime is slower. Therefore, execution time, speedup, and efficiency should be interpreted together.", styles)
    p(story, "The speedup is not linear. With 12 threads, a theoretical speedup of 12x might be expected, but this value is not reached in practice. The main reasons are the memory movement performed by the merge operation, the overhead of creating OpenMP tasks, and taskwait synchronization. During the merge step, data is moved between the main array and the temporary buffer, so memory access limits performance.", styles)

    h(story, "11. Conclusion", styles)
    p(story, "This study shows that the merge sort algorithm can be parallelized using OpenMP tasks. The independence of the left and right subarrays gives the algorithm a natural parallel structure. Correctness is verified using is_sorted and checksum. The threshold-based implementation provides better actual runtime than the no-threshold version for both tested input sizes, especially for the 50,000,000 element case.", styles)

    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    print(PDF_PATH)


if __name__ == "__main__":
    main()
