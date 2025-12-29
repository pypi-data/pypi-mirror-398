# %%
import pyopenms as oms
from pathlib import Path
import typer
from loguru import logger


# %%
app = typer.Typer(add_completion=False)

# %%
@app.command()
def get_mzml_ranges(
    input_path: Path = typer.Argument(..., help="Path to input mzML file"),
    output_path: Path = typer.Argument(None, help="Path to output tsv file (RT min, RT max, m/z min, m/z max)")
):
    """
    Get the RT (retention time) and MS1 m/z ranges from an mzML file.
    """
    logger.info(f"Reading file: {input_path}")
    
    if not input_path.exists():
        logger.error(f"File not found: {input_path}")
        raise typer.Exit(code=1)
    
    exp = oms.MSExperiment()
    oms.MzMLFile().load(str(input_path), exp)
    spectra = exp.getSpectra()
    
    # Filter MS1 spectra
    spectra_ms1 = [s for s in spectra if s.getMSLevel() == 1]
    
    if not spectra_ms1:
        logger.warning("No MS1 spectra found in the file")
        return
    
    # Get RT range
    rt_values = [s.getRT() for s in spectra_ms1]
    rt_min = min(rt_values)
    rt_max = max(rt_values)
    
    # Get m/z range
    mz_min = float('inf')
    mz_max = float('-inf')
    
    for spectrum in spectra_ms1:
        mz_array, _ = spectrum.get_peaks()
        if len(mz_array) > 0:
            mz_min = min(mz_min, mz_array.min())
            mz_max = max(mz_max, mz_array.max())
    
    logger.info(f"MS1 spectra count: {len(spectra_ms1)}")
    logger.info(f"RT range: {rt_min:.2f} - {rt_max:.2f} seconds")
    logger.info(f"m/z range: {mz_min:.4f} - {mz_max:.4f}")
    
    typer.echo(f"\nSummary:")
    typer.echo(f"  MS1 spectra: {len(spectra_ms1)}")
    typer.echo(f"  RT range: {rt_min:.2f} - {rt_max:.2f} seconds")
    typer.echo(f"  m/z range: {mz_min:.4f} - {mz_max:.4f}")
    if output_path:
        with open(output_path, 'w') as f:
            f.write(f"{rt_min}\t{rt_max}\t{mz_min}\t{mz_max}\n")
        logger.info(f"Summary written to: {output_path}")
    return rt_min, rt_max, mz_min, mz_max

# %%
@app.callback()
def callback():
    pass

if __name__ == "__main__":
    app()