import numpy as np
import random
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

def compare_algorithms(objective_function, products, iterations=50):
    """Benchmarks CATS against simple baselines."""
    # 1. Random Search
    rs_best = float('inf')
    for _ in range(iterations * 10):
        sol = random.sample(products, len(products))
        rs_best = min(rs_best, objective_function(sol))
    
    # 2. Nearest Neighbor (Heuristic)
    # Simplified version: Greedy choice
    curr = products[0]
    nn_sol = [curr]
    rem = products[1:]
    while rem:
        curr = min(rem, key=lambda x: objective_function([nn_sol[-1], x]))
        nn_sol.append(curr)
        rem.remove(curr)
    nn_best = objective_function(nn_sol)
    
    return {"Random Search": rs_best, "Nearest Neighbor": nn_best}

def generate_report(output_path, problem_name, description, parameters, best_solution, best_cost, benchmark_results):
    # PDF Generation
    pdf_file = f"{output_path}.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph(f"Optimization Report: {problem_name}", styles['Title']))
    elements.append(Paragraph(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Description
    elements.append(Paragraph("Problem Description:", styles['Heading2']))
    elements.append(Paragraph(description, styles['Normal']))
    elements.append(Spacer(1, 12))

    # Best Result
    elements.append(Paragraph(f"Best Cost Achieved: {best_cost:.4f}", styles['Heading3']))
    elements.append(Paragraph(f"Best Solution: {str(best_solution)}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Benchmark Table
    data = [["Algorithm", "Best Cost"]]
    data.append(["CATS (Our Model)", f"{best_cost:.4f}"])
    for algo, cost in benchmark_results.items():
        data.append([algo, f"{cost:.4f}"])

    table = Table(data, colWidths=[200, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    
    # Watermark
    elements.append(Spacer(1, 40))
    watermark_style = ParagraphStyle('Watermark', fontSize=10, textColor=colors.gray, alignment=1)
    elements.append(Paragraph("Made With Love: Louati Mahdi", watermark_style))

    doc.build(elements)

    # Excel Generation
    wb = Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(["Problem", problem_name])
    ws.append(["Best Cost", best_cost])
    ws.append([])
    ws.append(["Algorithm Comparison"])
    for algo, cost in benchmark_results.items():
        ws.append([algo, cost])
    ws.append([])
    ws.append(["Made With Love: Louati Mahdi"])
    wb.save(f"{output_path}.xlsx")
    
    print(f"Reports saved as {output_path}.pdf and {output_path}.xlsx")