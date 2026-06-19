# MRI Brain Tissue Analysis & Report Generator
# Stage 4 - Kuljit Singh

import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
from sklearn.cluster import KMeans
from nilearn import datasets
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
from datetime import datetime

print("=" * 50)
print("MRI Brain Tissue Analysis")
print("=" * 50)

# Step 1 - Load MRI scan
print("\nStep 1: Loading MRI scan...")
dataset = datasets.fetch_icbm152_2009()
img = nib.load(dataset.t1)
data = img.get_fdata()
print(f"Scan loaded! Shape: {data.shape}")

# Step 2 - Take middle slice and segment
print("\nStep 2: Segmenting brain tissue...")
slice_idx = data.shape[2] // 2
brain_slice = data[:, :, slice_idx]

pixels = brain_slice.flatten().reshape(-1, 1)
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
kmeans.fit(pixels)
labels = kmeans.labels_.reshape(brain_slice.shape)

# Sort clusters by brightness
centers = kmeans.cluster_centers_.flatten()
order = np.argsort(centers)
sorted_labels = np.zeros_like(labels)
for new_label, old_label in enumerate(order):
    sorted_labels[labels == old_label] = new_label

tissue_names = ['Background', 'Grey Matter', 'White Matter']
tissue_colors = ['#1a1aff', '#ff4444', '#ffff00']
print("Segmentation complete!")

# Step 3 - Measure each region
print("\nStep 3: Measuring tissue regions...")
total_pixels = sorted_labels.size
measurements = []

for i, name in enumerate(tissue_names):
    count = np.sum(sorted_labels == i)
    percentage = (count / total_pixels) * 100
    avg_brightness = np.mean(brain_slice[sorted_labels == i])
    measurements.append({
        'Tissue Type': name,
        'Voxel Count': int(count),
        'Percentage (%)': round(percentage, 2),
        'Avg Brightness': round(float(avg_brightness), 2)
    })
    print(f"  {name}: {count:,} voxels ({percentage:.1f}%)")

df = pd.DataFrame(measurements)
print("\nMeasurements complete!")

# Step 4 - Create charts
print("\nStep 4: Creating charts...")
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.patch.set_facecolor('#0a0a0a')

# Chart 1 - Original brain slice
axes[0].imshow(brain_slice.T, cmap='gray', origin='lower')
axes[0].set_title('Original MRI Slice', color='white', fontsize=12, fontweight='bold')
axes[0].axis('off')

# Chart 2 - Segmented slice
cmap = ListedColormap(tissue_colors)
axes[1].imshow(sorted_labels.T, cmap=cmap, origin='lower', vmin=0, vmax=2)
axes[1].set_title('Segmented Tissues', color='white', fontsize=12, fontweight='bold')
axes[1].axis('off')
patches = [mpatches.Patch(color=tissue_colors[i], label=tissue_names[i]) for i in range(3)]
axes[1].legend(handles=patches, loc='lower center', fontsize=8,
               facecolor='#1a1a1a', labelcolor='white')

# Chart 3 - Pie chart
percentages = [m['Percentage (%)'] for m in measurements]
axes[2].pie(percentages, labels=tissue_names, colors=tissue_colors,
            autopct='%1.1f%%', textprops={'color': 'white'})
axes[2].set_title('Tissue Distribution', color='white', fontsize=12, fontweight='bold')

plt.suptitle('MRI Brain Tissue Analysis -final kj',
             fontsize=14, fontweight='bold', color='white')
plt.tight_layout()
plt.savefig('analysis_charts.png', dpi=150, bbox_inches='tight',
            facecolor='#0a0a0a')
plt.close()
print("Charts saved!")

# Step 5 - Generate PDF report
print("\nStep 5: Generating PDF report...")
doc = SimpleDocTemplate("MRI_Analysis_Report.pdf", pagesize=A4,
                        leftMargin=2*cm, rightMargin=2*cm,
                        topMargin=2*cm, bottomMargin=2*cm)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('Title', fontSize=18, fontName='Helvetica-Bold',
                              alignment=TA_CENTER, spaceAfter=6,
                              textColor=colors.HexColor('#1a1a2e'))
subtitle_style = ParagraphStyle('Subtitle', fontSize=11, fontName='Helvetica',
                                 alignment=TA_CENTER, spaceAfter=20,
                                 textColor=colors.HexColor('#444444'))
heading_style = ParagraphStyle('Heading', fontSize=13, fontName='Helvetica-Bold',
                                spaceBefore=12, spaceAfter=6,
                                textColor=colors.HexColor('#1a1a2e'))
body_style = ParagraphStyle('Body', fontSize=10, fontName='Helvetica',
                             spaceAfter=6, leading=14)

story = []

# Title
story.append(Paragraph("MRI Brain Tissue Analysis Report", title_style))
story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", subtitle_style))
story.append(Paragraph(f"Analyst: Kuljit Singh | Otto Von Guericke University, Magdeburg", subtitle_style))
story.append(Spacer(1, 0.5*cm))

# Introduction
story.append(Paragraph("1. Introduction", heading_style))
story.append(Paragraph(
    "This report presents an automated analysis of MRI brain tissue segmentation using "
    "the ICBM152 standard brain template. K-means clustering was applied to classify "
    "brain tissue into three categories: background, grey matter, and white matter.",
    body_style))

# Charts
story.append(Paragraph("2. Visualisation", heading_style))
story.append(Image('analysis_charts.png', width=16*cm, height=5.5*cm))
story.append(Spacer(1, 0.3*cm))

# Measurements table
story.append(Paragraph("3. Tissue Measurements", heading_style))

table_data = [['Tissue Type', 'Voxel Count', 'Percentage (%)', 'Avg Brightness']]
for m in measurements:
    table_data.append([
        m['Tissue Type'],
        f"{m['Voxel Count']:,}",
        f"{m['Percentage (%)']:.2f}%",
        f"{m['Avg Brightness']:.2f}"
    ])

table = Table(table_data, colWidths=[4.5*cm, 3.5*cm, 4*cm, 4*cm])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f5f5f5'), colors.white]),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ('PADDING', (0, 0), (-1, -1), 8),
]))
story.append(table)
story.append(Spacer(1, 0.5*cm))

# Findings
story.append(Paragraph("4. Key Findings", heading_style))
dominant = max(measurements, key=lambda x: x['Percentage (%)'])
story.append(Paragraph(
    f"The analysis identified three distinct tissue regions. "
    f"The dominant region is {dominant['Tissue Type']} at {dominant['Percentage (%)']:.1f}% of the total slice area. "
    f"Grey matter and white matter together represent the active brain tissue regions, "
    f"with their ratio providing insight into brain structure and composition.",
    body_style))

story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("5. Methodology", heading_style))
story.append(Paragraph(
    "Segmentation was performed using K-means clustering (k=3) on pixel intensity values "
    "of the axial mid-brain slice. Clusters were sorted by mean brightness to ensure "
    "consistent tissue labelling across different scans. All measurements are based on "
    "2D slice analysis of the ICBM152 T1-weighted MRI template.",
    body_style))

doc.build(story)
print("PDF report generated: MRI_Analysis_Report.pdf")
print("\n" + "=" * 50)
print("Analysis Complete!")
print("=" * 50)