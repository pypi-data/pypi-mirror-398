#!/usr/bin/env python3
"""
Report Generator - Gerador de relatórios de segurança
Parte do toolkit Olho de Deus
"""

import os
import sys
import json
import html
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Finding:
    """Achado de segurança."""
    title: str
    severity: str  # critical, high, medium, low, info
    category: str
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendation: str = ""
    references: List[str] = field(default_factory=list)
    cvss_score: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "references": self.references,
            "cvss_score": self.cvss_score
        }


@dataclass
class ReportMetadata:
    """Metadados do relatório."""
    title: str
    author: str
    target: str
    scope: str
    start_date: str
    end_date: str
    executive_summary: str = ""
    methodology: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "author": self.author,
            "target": self.target,
            "scope": self.scope,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "executive_summary": self.executive_summary,
            "methodology": self.methodology
        }


class MarkdownReportGenerator:
    """Gerador de relatórios em Markdown."""
    
    SEVERITY_ICONS = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
        "info": "🔵"
    }
    
    @classmethod
    def generate(cls, metadata: ReportMetadata, findings: List[Finding]) -> str:
        """Gera relatório em Markdown."""
        lines = []
        
        # Header
        lines.append(f"# {metadata.title}")
        lines.append("")
        lines.append(f"**Autor:** {metadata.author}")
        lines.append(f"**Alvo:** {metadata.target}")
        lines.append(f"**Período:** {metadata.start_date} - {metadata.end_date}")
        lines.append(f"**Data do Relatório:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Table of Contents
        lines.append("## Índice")
        lines.append("")
        lines.append("1. [Sumário Executivo](#sumário-executivo)")
        lines.append("2. [Escopo](#escopo)")
        lines.append("3. [Metodologia](#metodologia)")
        lines.append("4. [Resumo de Achados](#resumo-de-achados)")
        lines.append("5. [Achados Detalhados](#achados-detalhados)")
        lines.append("6. [Conclusão](#conclusão)")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Executive Summary
        lines.append("## Sumário Executivo")
        lines.append("")
        if metadata.executive_summary:
            lines.append(metadata.executive_summary)
        else:
            # Auto-generate
            severity_counts = {s: 0 for s in cls.SEVERITY_ICONS}
            for f in findings:
                if f.severity in severity_counts:
                    severity_counts[f.severity] += 1
            
            lines.append(f"Este relatório apresenta os resultados da análise de segurança realizada em **{metadata.target}**.")
            lines.append("")
            lines.append(f"Foram identificados **{len(findings)}** achados:")
            for sev, count in severity_counts.items():
                if count > 0:
                    lines.append(f"- {cls.SEVERITY_ICONS[sev]} {sev.capitalize()}: {count}")
        lines.append("")
        
        # Scope
        lines.append("## Escopo")
        lines.append("")
        lines.append(metadata.scope or "Definido pelo cliente.")
        lines.append("")
        
        # Methodology
        lines.append("## Metodologia")
        lines.append("")
        lines.append(metadata.methodology or "Análise realizada utilizando ferramentas automatizadas e verificação manual.")
        lines.append("")
        
        # Findings Summary
        lines.append("## Resumo de Achados")
        lines.append("")
        lines.append("| # | Severidade | Título | Categoria |")
        lines.append("|---|------------|--------|-----------|")
        
        for i, finding in enumerate(findings, 1):
            icon = cls.SEVERITY_ICONS.get(finding.severity, "⚪")
            lines.append(f"| {i} | {icon} {finding.severity.upper()} | {finding.title} | {finding.category} |")
        
        lines.append("")
        
        # Detailed Findings
        lines.append("## Achados Detalhados")
        lines.append("")
        
        for i, finding in enumerate(findings, 1):
            icon = cls.SEVERITY_ICONS.get(finding.severity, "⚪")
            lines.append(f"### {i}. {icon} {finding.title}")
            lines.append("")
            lines.append(f"**Severidade:** {finding.severity.upper()}")
            lines.append(f"**Categoria:** {finding.category}")
            if finding.cvss_score:
                lines.append(f"**CVSS:** {finding.cvss_score}")
            lines.append("")
            
            lines.append("**Descrição:**")
            lines.append(finding.description)
            lines.append("")
            
            if finding.evidence:
                lines.append("**Evidência:**")
                lines.append("```")
                for ev in finding.evidence:
                    lines.append(ev)
                lines.append("```")
                lines.append("")
            
            if finding.recommendation:
                lines.append("**Recomendação:**")
                lines.append(finding.recommendation)
                lines.append("")
            
            if finding.references:
                lines.append("**Referências:**")
                for ref in finding.references:
                    lines.append(f"- {ref}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # Conclusion
        lines.append("## Conclusão")
        lines.append("")
        lines.append("As vulnerabilidades identificadas devem ser corrigidas de acordo com sua severidade.")
        lines.append("Recomenda-se priorizar os achados críticos e de alta severidade.")
        lines.append("")
        lines.append("---")
        lines.append(f"*Relatório gerado por Olho de Deus em {datetime.now().isoformat()}*")
        
        return "\n".join(lines)


class HTMLReportGenerator:
    """Gerador de relatórios em HTML."""
    
    SEVERITY_COLORS = {
        "critical": "#dc3545",
        "high": "#fd7e14",
        "medium": "#ffc107",
        "low": "#28a745",
        "info": "#17a2b8"
    }
    
    TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        header {{ background: #2c3e50; color: white; padding: 30px; margin-bottom: 30px; }}
        header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        header .meta {{ display: flex; flex-wrap: wrap; gap: 20px; font-size: 0.9em; opacity: 0.9; }}
        h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin: 30px 0 20px; }}
        h3 {{ color: #34495e; margin: 20px 0 10px; }}
        .summary-box {{ display: flex; gap: 20px; flex-wrap: wrap; margin: 20px 0; }}
        .stat {{ padding: 20px; border-radius: 8px; color: white; text-align: center; min-width: 120px; }}
        .stat .count {{ font-size: 2em; font-weight: bold; }}
        .stat .label {{ font-size: 0.9em; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .finding {{ background: #fff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px 0; overflow: hidden; }}
        .finding-header {{ padding: 15px 20px; color: white; display: flex; justify-content: space-between; align-items: center; }}
        .finding-body {{ padding: 20px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; text-transform: uppercase; }}
        .evidence {{ background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: monospace; overflow-x: auto; white-space: pre-wrap; }}
        .recommendation {{ background: #e8f4fd; border-left: 4px solid #3498db; padding: 15px; margin: 15px 0; }}
        footer {{ text-align: center; padding: 30px; color: #666; border-top: 1px solid #ddd; margin-top: 50px; }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{title}</h1>
            <div class="meta">
                <span>👤 {author}</span>
                <span>🎯 {target}</span>
                <span>📅 {start_date} - {end_date}</span>
            </div>
        </div>
    </header>
    
    <div class="container">
        {content}
    </div>
    
    <footer>
        <p>Relatório gerado por <strong>Olho de Deus</strong> em {generated_at}</p>
    </footer>
</body>
</html>"""
    
    @classmethod
    def generate(cls, metadata: ReportMetadata, findings: List[Finding]) -> str:
        """Gera relatório em HTML."""
        content_parts = []
        
        # Summary
        content_parts.append("<h2>Sumário Executivo</h2>")
        
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for f in findings:
            if f.severity in severity_counts:
                severity_counts[f.severity] += 1
        
        content_parts.append('<div class="summary-box">')
        for sev, count in severity_counts.items():
            color = cls.SEVERITY_COLORS[sev]
            content_parts.append(f'''
                <div class="stat" style="background: {color}">
                    <div class="count">{count}</div>
                    <div class="label">{sev}</div>
                </div>
            ''')
        content_parts.append('</div>')
        
        if metadata.executive_summary:
            content_parts.append(f"<p>{html.escape(metadata.executive_summary)}</p>")
        
        # Scope
        content_parts.append("<h2>Escopo</h2>")
        content_parts.append(f"<p>{html.escape(metadata.scope)}</p>")
        
        # Findings Table
        content_parts.append("<h2>Resumo de Achados</h2>")
        content_parts.append("""
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Severidade</th>
                        <th>Título</th>
                        <th>Categoria</th>
                    </tr>
                </thead>
                <tbody>
        """)
        
        for i, finding in enumerate(findings, 1):
            color = cls.SEVERITY_COLORS.get(finding.severity, "#999")
            content_parts.append(f"""
                <tr>
                    <td>{i}</td>
                    <td><span class="badge" style="background: {color}; color: white;">{finding.severity}</span></td>
                    <td>{html.escape(finding.title)}</td>
                    <td>{html.escape(finding.category)}</td>
                </tr>
            """)
        
        content_parts.append("</tbody></table>")
        
        # Detailed Findings
        content_parts.append("<h2>Achados Detalhados</h2>")
        
        for i, finding in enumerate(findings, 1):
            color = cls.SEVERITY_COLORS.get(finding.severity, "#999")
            
            content_parts.append(f'''
                <div class="finding">
                    <div class="finding-header" style="background: {color}">
                        <h3>{i}. {html.escape(finding.title)}</h3>
                        <span class="badge" style="background: rgba(255,255,255,0.2)">{finding.severity.upper()}</span>
                    </div>
                    <div class="finding-body">
                        <p><strong>Categoria:</strong> {html.escape(finding.category)}</p>
                        {"<p><strong>CVSS:</strong> " + str(finding.cvss_score) + "</p>" if finding.cvss_score else ""}
                        
                        <h4>Descrição</h4>
                        <p>{html.escape(finding.description)}</p>
            ''')
            
            if finding.evidence:
                content_parts.append('<h4>Evidência</h4><div class="evidence">')
                for ev in finding.evidence:
                    content_parts.append(html.escape(ev) + "\n")
                content_parts.append('</div>')
            
            if finding.recommendation:
                content_parts.append(f'''
                    <h4>Recomendação</h4>
                    <div class="recommendation">{html.escape(finding.recommendation)}</div>
                ''')
            
            content_parts.append('</div></div>')
        
        content = "\n".join(content_parts)
        
        return cls.TEMPLATE.format(
            title=html.escape(metadata.title),
            author=html.escape(metadata.author),
            target=html.escape(metadata.target),
            start_date=html.escape(metadata.start_date),
            end_date=html.escape(metadata.end_date),
            content=content,
            generated_at=datetime.now().isoformat()
        )


class JSONReportGenerator:
    """Gerador de relatórios em JSON."""
    
    @classmethod
    def generate(cls, metadata: ReportMetadata, findings: List[Finding]) -> str:
        """Gera relatório em JSON."""
        report = {
            "metadata": metadata.to_dict(),
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_findings": len(findings),
                "by_severity": {
                    "critical": sum(1 for f in findings if f.severity == "critical"),
                    "high": sum(1 for f in findings if f.severity == "high"),
                    "medium": sum(1 for f in findings if f.severity == "medium"),
                    "low": sum(1 for f in findings if f.severity == "low"),
                    "info": sum(1 for f in findings if f.severity == "info"),
                }
            },
            "findings": [f.to_dict() for f in findings]
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)


class ReportGenerator:
    """Gerador principal de relatórios."""
    
    def __init__(self):
        self.metadata = None
        self.findings: List[Finding] = []
    
    def set_metadata(self, metadata: ReportMetadata):
        """Define metadados do relatório."""
        self.metadata = metadata
    
    def add_finding(self, finding: Finding):
        """Adiciona um achado."""
        self.findings.append(finding)
    
    def generate_markdown(self) -> str:
        """Gera relatório em Markdown."""
        if not self.metadata:
            raise ValueError("Metadata não definida")
        return MarkdownReportGenerator.generate(self.metadata, self.findings)
    
    def generate_html(self) -> str:
        """Gera relatório em HTML."""
        if not self.metadata:
            raise ValueError("Metadata não definida")
        return HTMLReportGenerator.generate(self.metadata, self.findings)
    
    def generate_json(self) -> str:
        """Gera relatório em JSON."""
        if not self.metadata:
            raise ValueError("Metadata não definida")
        return JSONReportGenerator.generate(self.metadata, self.findings)
    
    def save(self, filename: str, format: str = "markdown"):
        """Salva relatório em arquivo."""
        if format == "markdown":
            content = self.generate_markdown()
            ext = ".md"
        elif format == "html":
            content = self.generate_html()
            ext = ".html"
        elif format == "json":
            content = self.generate_json()
            ext = ".json"
        else:
            raise ValueError(f"Formato desconhecido: {format}")
        
        if not filename.endswith(ext):
            filename += ext
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename


def interactive_menu():
    """Menu interativo do Report Generator."""
    generator = ReportGenerator()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        findings_count = len(generator.findings)
        meta_status = "✅" if generator.metadata else "❌"
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║          📊 REPORT GENERATOR - Olho de Deus                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Metadata: {meta_status}    Achados: {findings_count}                                ║
║                                                              ║
║  [1] 📝 Definir Metadata do Relatório                        ║
║  [2] ➕ Adicionar Achado                                     ║
║  [3] 📋 Listar Achados                                       ║
║  [4] 📄 Gerar Relatório Markdown                             ║
║  [5] 🌐 Gerar Relatório HTML                                 ║
║  [6] 📊 Gerar Relatório JSON                                 ║
║  [7] 💾 Salvar Relatório                                     ║
║  [8] 📁 Importar Achados de JSON                             ║
║                                                              ║
║  [0] Voltar                                                  ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        escolha = input("Opção: ").strip()
        
        if escolha == '0':
            break
        
        elif escolha == '1':
            print("\n=== Definir Metadata ===")
            
            title = input("Título do relatório: ").strip() or "Relatório de Segurança"
            author = input("Autor: ").strip() or "Security Team"
            target = input("Alvo: ").strip() or "Target System"
            scope = input("Escopo: ").strip() or "Análise de vulnerabilidades"
            start_date = input("Data início (YYYY-MM-DD): ").strip() or datetime.now().strftime("%Y-%m-%d")
            end_date = input("Data fim (YYYY-MM-DD): ").strip() or datetime.now().strftime("%Y-%m-%d")
            
            print("\nSumário Executivo (Enter para auto-gerar):")
            summary = input().strip()
            
            generator.set_metadata(ReportMetadata(
                title=title,
                author=author,
                target=target,
                scope=scope,
                start_date=start_date,
                end_date=end_date,
                executive_summary=summary
            ))
            
            print("✅ Metadata definida!")
        
        elif escolha == '2':
            print("\n=== Adicionar Achado ===")
            
            title = input("Título: ").strip()
            if not title:
                continue
            
            print("\nSeveridade: critical, high, medium, low, info")
            severity = input("Severidade: ").strip().lower() or "medium"
            
            category = input("Categoria: ").strip() or "Geral"
            description = input("Descrição: ").strip()
            
            print("\nEvidências (Enter para terminar):")
            evidence = []
            while True:
                ev = input("  > ").strip()
                if not ev:
                    break
                evidence.append(ev)
            
            recommendation = input("Recomendação: ").strip()
            
            cvss_str = input("CVSS Score (ou Enter): ").strip()
            cvss = float(cvss_str) if cvss_str else None
            
            finding = Finding(
                title=title,
                severity=severity,
                category=category,
                description=description,
                evidence=evidence,
                recommendation=recommendation,
                cvss_score=cvss
            )
            
            generator.add_finding(finding)
            print(f"✅ Achado '{title}' adicionado!")
        
        elif escolha == '3':
            print("\n=== Achados ===\n")
            
            if not generator.findings:
                print("Nenhum achado registrado.")
            else:
                icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}
                for i, f in enumerate(generator.findings, 1):
                    icon = icons.get(f.severity, "⚪")
                    print(f"{i}. {icon} [{f.severity.upper()}] {f.title}")
                    print(f"   Categoria: {f.category}")
                    if f.cvss_score:
                        print(f"   CVSS: {f.cvss_score}")
                    print()
        
        elif escolha == '4':
            if not generator.metadata:
                print("❌ Defina os metadados primeiro!")
                input("Enter para continuar...")
                continue
            
            print("\n=== Preview Markdown ===\n")
            md = generator.generate_markdown()
            print(md[:2000])
            if len(md) > 2000:
                print(f"\n... ({len(md)} caracteres total)")
        
        elif escolha == '5':
            if not generator.metadata:
                print("❌ Defina os metadados primeiro!")
                input("Enter para continuar...")
                continue
            
            print("\n=== Gerando HTML ===")
            html_content = generator.generate_html()
            
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Salvo em {filename}")
        
        elif escolha == '6':
            if not generator.metadata:
                print("❌ Defina os metadados primeiro!")
                input("Enter para continuar...")
                continue
            
            print("\n=== JSON ===\n")
            json_content = generator.generate_json()
            print(json_content[:2000])
        
        elif escolha == '7':
            if not generator.metadata:
                print("❌ Defina os metadados primeiro!")
                input("Enter para continuar...")
                continue
            
            print("\n=== Salvar Relatório ===")
            print("1. Markdown")
            print("2. HTML")
            print("3. JSON")
            fmt = input("Formato: ").strip()
            
            filename = input("Nome do arquivo: ").strip() or f"report_{datetime.now().strftime('%Y%m%d')}"
            
            fmt_map = {"1": "markdown", "2": "html", "3": "json"}
            if fmt in fmt_map:
                saved = generator.save(filename, fmt_map[fmt])
                print(f"✅ Salvo em {saved}")
        
        elif escolha == '8':
            print("\n=== Importar de JSON ===")
            file_path = input("Caminho do arquivo: ").strip()
            
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                finding = Finding(
                                    title=item.get("title", "Sem título"),
                                    severity=item.get("severity", "medium"),
                                    category=item.get("category", "Geral"),
                                    description=item.get("description", ""),
                                    evidence=item.get("evidence", []),
                                    recommendation=item.get("recommendation", ""),
                                    cvss_score=item.get("cvss_score")
                                )
                                generator.add_finding(finding)
                        print(f"✅ {len(data)} achados importados!")
                except Exception as e:
                    print(f"❌ Erro: {e}")
            else:
                print("❌ Arquivo não encontrado")
        
        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    interactive_menu()
