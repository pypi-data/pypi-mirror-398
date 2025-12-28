from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from enum import Enum
from pydantic import BaseModel, Field

class cfrna_mcp_tools(str, Enum):
    run_fastq_quality_control = 'run_fastq_quality_control'
    run_genome_mapping = 'run_genome_mapping'
    run_calculate_expression = 'run_calculate_expression'
    run_deg = 'run_deg'
    run_go_enrichment = 'run_go_enrichment'
    run_kegg_enrichment = 'run_kegg_enrichment'
    run_chromosome_diagnosis = 'run_chromosome_diagnosis'
    run_tumor_diagnosis = 'run_tumor_diagnosis'
    run_donor_diagnosis = 'run_donor_diagnosis'
    run_cell_tracing = 'run_cell_tracing'
    run_find_biomarker = 'run_find_biomarker'


class run_fastq_quality_control_inputs(BaseModel):
    raw_fastq_file_1: str = Field(description = '原始测序数据的 read 1 fastq 文件路径（.fq.gz 格式）')
    raw_fastq_file_2: str = Field(description = '原始测序数据的 read 2 fastq 文件路径（.fq.gz 格式）')
    sample_name: str = Field(description = '样品名称')
    trim_front_1: int = Field(description = 'read 1 前端切除碱基数量；参数范围：0-10；默认：0')
    trim_front_2: int = Field(description = 'read 2 前端切除碱基数量；参数范围：0-10；默认：0')
    trim_tail_1: int = Field(description = 'read 1 末端切除碱基数量；参数范围：0-10；默认：0')
    trim_tail_2: int = Field(description = 'read 2 末端切除碱基数量；参数范围：0-10；默认：0')

class run_fastq_quality_control_outputs(BaseModel):
    clean_fastq_file_1: str = Field(description = '经过质控处理的 read 1 fastq 文件路径（.fq.gz 格式）')
    clean_fastq_file_2: str = Field(description = '经过质控处理的 read 2 fastq 文件路径（.fq.gz 格式）')
    qc_statistic_file: str = Field(description = '原始数据质控统计结果文件（.txt 格式）')

def run_fastq_quality_control(
        raw_fastq_file_1: str,
        raw_fastq_file_2: str,
        sample_name: str,
        trim_front_1: int = 0,
        trim_front_2: int = 0,
        trim_tail_1: int = 0,
        trim_tail_2: int = 0
    ) -> dict:
    return dict(
        clean_fastq_file_1 = f"/output/result/{sample_name}/clean_1.fq.gz",
        clean_fastq_file_2 = f"/output/result/{sample_name}/clean_2.fq.gz"
    )


class run_genome_mapping_inputs(BaseModel):
    clean_fastq_file_1: str = Field(description = '经过质控处理的 read 1 fastq 文件路径（.fq.gz 格式）')
    clean_fastq_file_2: str = Field(description = '经过质控处理的 read 2 fastq 文件路径（.fq.gz 格式）')
    sample_name: str = Field(description = '样品名称')
    genome: str = Field(description = '参考基因组；可选内容：human, mouse；默认：human')

class run_genome_mapping_outputs(BaseModel):
    bam_file: str = Field(description = '参考基因组比对生成的 bam 文件（.bam 格式）')
    qc_statistic_file: str = Field(description = '参考基因组比对情况统计结果文件（.txt 格式）')

def run_genome_mapping(
        clean_fastq_file_1: str,
        clean_fastq_file_2: str,
        sample_name: str,
        genome: str = "human"
    ) -> dict:
    return dict(
        bam_file = f"/output/result/{sample_name}/mapping.bam",
        qc_statistic_file = f"/output/result/{sample_name}/qc_statistic.txt"
    )


class run_calculate_expression_inputs(BaseModel):
    bam_file: list[str] = Field(description = '所有样品的参考基因组比对生成的 bam 文件（.bam 格式）')
    genome: str = Field(description = '参考基因组；可选内容：human, mouse；默认：human')
    method: str = Field(description = '表达量计算方法；可选内容：m1, m2；默认：m1')

class run_calculate_expression_outputs(BaseModel):
    tpm_file: str = Field(description = '所有样品的 TPM 格式表达量矩阵文件（.txt 格式）')
    count_file: str = Field(description = '所有样品的 Count 格式表达量矩阵文件（.txt 格式）')

def run_calculate_expression(
        bam_file: list[str],
        genome: str = "human",
        method: str = "m1"
    ) -> dict:
    return dict(
        tpm_file = f"/output/result/expression/TPM_{method}.txt",
        count_file = f"/output/result/expression/Count_{method}.txt"
    )


class run_deg_inputs(BaseModel):
    tpm_file: str = Field(description = '所有样品的 TPM 格式表达量矩阵文件（.txt 格式）')
    count_file: str = Field(description = '所有样品的 Count 格式表达量矩阵文件（.txt 格式）')
    group_file: str = Field(description = '分组文件（.txt 格式）')
    method: str = Field(description = '差异表达分析方法；可选内容：m1, m2, m3；默认：m1')
    cutoff_logfc: float = Field(description = 'log2FC 阈值；参数范围：0.5-2；默认：1')
    cutoff_pvalue: float = Field(description = 'p 值阈值；参数范围：0-1；默认：0.05')
    cutoff_qvalue: float = Field(description = 'q 值阈值；参数范围：0-1；默认：0.05')

class run_deg_outputs(BaseModel):
    deg_file: str = Field(description = '差异表达分析结果文件（.txt 格式）')

def run_deg(
        tpm_file: str,
        count_file: str,
        group_file: str,
        method: str = "m1",
        cutoff_logfc: float = 1,
        cutoff_pvalue: float = 0.05,
        cutoff_qvalue: float = 0.05
    ) -> dict:
    return dict(
        deg_file = f"/output/result/deg/deg_result_{method}.txt"
    )


class run_go_enrichment_inputs(BaseModel):
    deg_file: str = Field(description = '差异表达分析结果文件（.txt 格式）')
    genome: str = Field(description = '参考基因组；可选内容：human, mouse；默认：human')
    cutoff_pvalue: float = Field(description = 'p 值阈值；参数范围：0-1；默认：0.05')
    cutoff_qvalue: float = Field(description = 'q 值阈值；参数范围：0-1；默认：0.05')

class run_go_enrichment_outputs(BaseModel):
    go_file: str = Field(description = 'GO 富集分析结果文件（.txt 格式）')

def run_go_enrichment(
        deg_file: str,
        genome: str = "human",
        cutoff_pvalue: float = 0.05,
        cutoff_qvalue: float = 0.05
    ) -> dict:
    return dict(
        go_file = f"/output/result/go/go_result.txt"
    )


class run_kegg_enrichment_inputs(BaseModel):
    deg_file: str = Field(description = '差异表达分析结果文件（.txt 格式）')
    genome: str = Field(description = '参考基因组；可选内容：human, mouse；默认：human')
    cutoff_pvalue: float = Field(description = 'p 值阈值；参数范围：0-1；默认：0.05')
    cutoff_qvalue: float = Field(description = 'q 值阈值；参数范围：0-1；默认：0.05')

class run_kegg_enrichment_outputs(BaseModel):
    kegg_file: str = Field(description = 'KEGG 富集分析结果文件（.txt 格式）')

def run_kegg_enrichment(
        deg_file: str,
        genome: str = "human",
        cutoff_pvalue: float = 0.05,
        cutoff_qvalue: float = 0.05
    ) -> dict:
    return dict(
        kegg_file = f"/output/result/kegg/kegg_result.txt"
    )


class run_chromosome_diagnosis_inputs(BaseModel):
    tpm_file: str = Field(description = '所有样品的 TPM 格式表达量矩阵文件（.txt 格式）')
    genome: str = Field(description = '参考基因组；可选内容：human, mouse；默认：human')
    all_chr: bool = Field(description = '选择对基因组包含的所有染色体都进行分析还是仅对常见染色体进行分析，可选内容：True, False，默认：True')

class run_chromosome_diagnosis_outputs(BaseModel):
    chromosome_diagnosis_file: str = Field(description = '染色体诊断分析结果文件（.txt 格式）')

def run_chromosome_diagnosis(
        tpm_file: str,
        genome: str = "human",
        all_chr: bool = True
    ) -> dict:
    return dict(
        chromosome_diagnosis_file = f"/output/result/chromosome_diagnosis/chromosome_diagnosis_result.txt"
    )


class run_tumor_diagnosis_inputs(BaseModel):
    tpm_file: str = Field(description = '所有样品的 TPM 格式表达量矩阵文件（.txt 格式）')
    genome: str = Field(description = '参考基因组；可选内容：human, mouse；默认：human')
    cutoff_tpm: float = Field(description = 'TPM 阈值，所有样品的 TPM 值均低于该值的基因将会丢弃；参数范围：0-5；默认：1')

class run_tumor_diagnosis_outputs(BaseModel):
    tumor_diagnosis_file: str = Field(description = '肿瘤诊断分析结果文件（.txt 格式）')

def run_tumor_diagnosis(
        tpm_file: str,
        genome: str = "human",
        cutoff_tpm: float = 1
    ) -> dict:
    return dict(
        tumor_diagnosis_file = f"/output/result/tumor_diagnosis/tumor_diagnosis_result.txt"
    )


class run_donor_diagnosis_inputs(BaseModel):
    tpm_file: str = Field(description = '所有样品的 TPM 格式表达量矩阵文件（.txt 格式）')
    genome: str = Field(description = '参考基因组；可选内容：human, mouse；默认：human')
    sensitivity: float = Field(description = '灵敏度，灵敏度越高，分析速度越慢；参数范围：0-1；默认：0.5')

class run_donor_diagnosis_outputs(BaseModel):
    donor_diagnosis_file: str = Field(description = '免疫排斥反应分析结果文件（.txt 格式）')

def run_donor_diagnosis(
        tpm_file: str,
        genome: str = "human",
        sensitivity: float = 0.5
    ) -> dict:
    return dict(
        donor_diagnosis_file = f"/output/result/donor_diagnosis/donor_diagnosis_result.txt"
    )


class run_cell_tracing_inputs(BaseModel):
    tpm_file: str = Field(description = '所有样品的 TPM 格式表达量矩阵文件（.txt 格式）')
    genome: str = Field(description = '参考基因组；可选内容：human, mouse；默认：human')
    method: str = Field(description = '选择不同的分析方法；可选内容：m1,m2；默认：m1')

class run_cell_tracing_outputs(BaseModel):
    cell_tracing_file: str = Field(description = '细胞溯源分析结果文件（.txt 格式）')

def run_cell_tracing(
        tpm_file: str,
        genome: str = "human",
        method: str = "m1"
    ) -> dict:
    return dict(
        cell_tracing_file = f"/output/result/cell_tracing/cell_tracing_result_{method}.txt"
    )


class run_find_biomarker_inputs(BaseModel):
    tpm_file: str = Field(description = '所有样品的 TPM 格式表达量矩阵文件（.txt 格式）')
    genome: str = Field(description = '参考基因组；可选内容：human, mouse；默认：human')
    model: str = Field(description = '选择想要使用哪个模型进行分析；可选内容：m1,m2,m3,m4；默认：m1')
    filter_low: bool = Field(description = '分析之前是否过滤掉低表达的基因，可选内容：True,False；默认：True')

class run_find_biomarker_outputs(BaseModel):
    biomarker_file: str = Field(description = 'biomarker 分析结果文件（.txt 格式）')

def run_find_biomarker(
        tpm_file: str,
        genome: str = "human",
        model: str = "m1",
        filter_low: bool = True
    ) -> dict:
    return dict(
        biomarker_file = f"/output/result/biomarker/biomarker_result_{model}.txt"
    )


async def mcp_server() -> None:
    server = Server("cfRNA MCP server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=cfrna_mcp_tools.run_fastq_quality_control,
                description=""" 原始数据质控：去除接头序列并统计数据质量 """,
                inputSchema=run_fastq_quality_control_inputs.model_json_schema(),
            ),
            Tool(
                name=cfrna_mcp_tools.run_genome_mapping,
                description=""" 参考基因组比对 """,
                inputSchema=run_genome_mapping_inputs.model_json_schema(),
            ),
            Tool(
                name=cfrna_mcp_tools.run_calculate_expression,
                description=""" 基因表达定量：同时生成 Count 和 TPM 格式的基因表达量 """,
                inputSchema=run_calculate_expression_inputs.model_json_schema(),
            ),
            Tool(
                name=cfrna_mcp_tools.run_deg,
                description=""" 差异表达分析：获取表达量发生显著变化的基因 """,
                inputSchema=run_deg_inputs.model_json_schema(),
            ),
            Tool(
                name=cfrna_mcp_tools.run_go_enrichment,
                description=""" GO 富集分析 """,
                inputSchema=run_go_enrichment_inputs.model_json_schema(),
            ),
            Tool(
                name=cfrna_mcp_tools.run_kegg_enrichment,
                description=""" KEGG 富集分析 """,
                inputSchema=run_kegg_enrichment_inputs.model_json_schema(),
            ),
            Tool(
                name=cfrna_mcp_tools.run_chromosome_diagnosis,
                description=""" 染色体诊断分析：检查样品是否患有染色体异常疾病 """,
                inputSchema=run_chromosome_diagnosis_inputs.model_json_schema(),
            ),
            Tool(
                name=cfrna_mcp_tools.run_tumor_diagnosis,
                description=""" 肿瘤诊断分析：检查样品是否包含肿瘤片段 """,
                inputSchema=run_tumor_diagnosis_inputs.model_json_schema(),
            ),
            Tool(
                name=cfrna_mcp_tools.run_donor_diagnosis,
                description=""" 供体诊断分析：检查器官移植是否发生排斥反应及其反应程度 """,
                inputSchema=run_donor_diagnosis_inputs.model_json_schema(),
            ),
            Tool(
                name=cfrna_mcp_tools.run_cell_tracing,
                description=""" 细胞溯源分析：分析样品中不同类型的细胞比例 """,
                inputSchema=run_cell_tracing_inputs.model_json_schema(),
            ),
            Tool(
                name=cfrna_mcp_tools.run_find_biomarker,
                description=""" 生物标记物分析：通过机器学习分析多个样品中关键的生物标记物 """,
                inputSchema=run_find_biomarker_inputs.model_json_schema(),
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        match name:
            case cfrna_mcp_tools.run_fastq_quality_control:
                return run_fastq_quality_control(
                    raw_fastq_file_1 = arguments["raw_fastq_file_1"],
                    raw_fastq_file_2 = arguments["raw_fastq_file_2"],
                    sample_name = arguments["sample_name"]
                )

            case cfrna_mcp_tools.run_genome_mapping:
                return run_genome_mapping(
                    clean_fastq_file_1 = arguments["clean_fastq_file_1"],
                    clean_fastq_file_2 = arguments["clean_fastq_file_2"],
                    sample_name = arguments["sample_name"]
                )

            case cfrna_mcp_tools.run_calculate_expression:
                return run_calculate_expression(
                    bam_file = arguments["bam_file"]
                )
            
            case cfrna_mcp_tools.run_deg:
                return run_deg(
                    tpm_file = arguments["tpm_file"],
                    count_file = arguments["count_file"],
                    group_file = arguments["group_file"]
                )

            case cfrna_mcp_tools.run_go_enrichment:
                return run_go_enrichment(
                    deg_file = str(arguments["deg_file"])
                )

            case cfrna_mcp_tools.run_kegg_enrichment:
                return run_kegg_enrichment(
                    deg_file = str(arguments["deg_file"])
                )
            
            case cfrna_mcp_tools.run_chromosome_diagnosis:
                return run_chromosome_diagnosis(
                    tpm_file = arguments["tpm_file"]
                )

            case cfrna_mcp_tools.run_tumor_diagnosis:
                return run_tumor_diagnosis(
                    tpm_file = arguments["tpm_file"]
                )

            case cfrna_mcp_tools.run_donor_diagnosis:
                return run_donor_diagnosis(
                    tpm_file = arguments["tpm_file"]
                )

            case cfrna_mcp_tools.run_cell_tracing:
                return run_cell_tracing(
                    tpm_file = arguments["tpm_file"]
                )

            case cfrna_mcp_tools.run_find_biomarker:
                return run_find_biomarker(
                    tpm_file = arguments["tpm_file"]
                )

            case _:
                raise ValueError(f"Unknown tool: {name}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
