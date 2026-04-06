#!/bin/bash

# =========================
# USER CONFIG - EDIT ONLY THIS SECTION
# =========================
INPUTS=(
    "/nfs/fanae/user/jprado/Prado/Firmware_Emulator_test/Root_files/"
)

CHUNK_SIZE=24 # number of files per chunk
COMMAND="python dump_events.py" # command to run on each chunk, should accept file list as arguments with -i 
ARGS="-o ntuples/dumped-roots-jpshowers/events_dumped___TASK_ID__.root -cf yamls/dumper_run_config_v2.yaml" # additional args for the command, __TASK_ID__ will be replaced by the chunk id (starting from 0)
CONDA_ENV="showers-destrada" # name of conda environment to activate before running the command, set to "none" if env not needed
LOG_DIR="logs" # directory to store logs, each chunk will have job_<id>.out and job_<id>.err files
CPUS=1 # number of CPUs to request for each job (only applies if USE_SLURM=true)

# =========================
# Args parsing
# =========================

USE_SLURM=false
USE_SCREEN=false # only applies if USE_SLURM=false
DRY_RUN=false
USER_RUN=""

print_usage() {
    cat <<EOF
Usage: bash "launch_cmd_on_chunks.sh" [options]

Options:
  --mode <slurm|screen|local>  Execution mode (default: local).
  --run <N>                    Target a specific run directory (run_N).
  --dry-run                    Print commands without submitting/running jobs.
  --retry                      Retry chunks with a non-empty .err log.
                               Uses last run dir unless --run is specified.
  -h, --help                   Show this help message.

Examples:
  bash launch_cmd_on_chunks.sh --mode slurm --dry-run
  bash launch_cmd_on_chunks.sh --mode screen
  bash launch_cmd_on_chunks.sh --retry
  bash launch_cmd_on_chunks.sh --retry --run 3
EOF
}

MODE=""
RETRY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            [ -z "${2:-}" ] && echo "Missing value for --mode" && print_usage && exit 1
            MODE="$2"
            shift 2
            ;;
        --mode=*)
            MODE="${1#*=}"
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --retry)
            RETRY=true
            shift
            ;;
        --run)
            [ -z "${2:-}" ] && echo "Missing value for --run" && print_usage && exit 1
            USER_RUN="$2"
            shift 2
            ;;
        --run=*)
            USER_RUN="${1#*=}"
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

if [ -n "$MODE" ]; then
    case "$MODE" in
        slurm)
            USE_SLURM=true
            ;;
        screen)
            USE_SLURM=false
            USE_SCREEN=true
            ;;
        local)
            USE_SLURM=false
            USE_SCREEN=false
            ;;
        *)
            echo "Invalid mode: $MODE"
            echo "Valid values: slurm, screen, local"
            exit 1
            ;;
    esac
fi

# =========================
# RESOLVE RUN INDEX
# =========================
# find next run_X index by scanning existing dirs or use provided --run value
RUN_ID="${USER_RUN:-0}"
while [[ -z "$USER_RUN" && -d "$LOG_DIR/run_$RUN_ID" ]]; do
    (( RUN_ID++ ))
done
# validate provided --run value
[ -n "$USER_RUN" ] && [ ! -d "$LOG_DIR/run_$RUN_ID" ] && echo "Run $USER_RUN not found in $LOG_DIR" && exit 1

if [ "$RETRY" = true ] && [ -z "$USER_RUN" ]; then
    RUN_ID=$(( RUN_ID - 1 ))
    [ "$RUN_ID" -lt 0 ] && echo "No previous run found to retry." && exit 1
fi

RUN_DIR="$LOG_DIR/run_$RUN_ID"
mkdir -p "$RUN_DIR"
echo "Run directory: $RUN_DIR"

# =========================
# RESOLVE FILES
# =========================
FILES=()

for item in "${INPUTS[@]}"; do
    if [[ -d "$item" ]]; then
        while IFS= read -r -d '' f; do
            FILES+=("$f")
        done < <(find "$item" -type f -print0)

    elif [[ -f "$item" ]]; then
        FILES+=("$item")

    else
        for f in $item; do
            [[ -f "$f" ]] && FILES+=("$f")
        done
    fi
done

mapfile -t FILES < <(printf "%s\n" "${FILES[@]}" | sort -V | awk '!seen[$0]++')

N_FILES=${#FILES[@]}
[ "$N_FILES" -eq 0 ] && echo "No files found" && exit 1

N_CHUNKS=$(( (N_FILES + CHUNK_SIZE - 1) / CHUNK_SIZE ))

echo "Files: $N_FILES → Chunks: $N_CHUNKS"

# =========================
# CHUNKS TO RUN
# =========================

CHUNK_IDS=()

if [ "$RETRY" = true ]; then
    echo "Retrying run_$RUN_ID"
    for ((i=0; i<N_CHUNKS; i++)); do
        [[ -s "$RUN_DIR/job_$i.err" ]] && CHUNK_IDS+=("$i")
    done
    [ ${#CHUNK_IDS[@]} -eq 0 ] && echo "No failed jobs found in $RUN_DIR." && exit 0
    echo "Retrying ${#CHUNK_IDS[@]} failed chunks: ${CHUNK_IDS[*]}"
else
    for ((i=0; i<N_CHUNKS; i++)); do
        CHUNK_IDS+=("$i")
    done
fi

# =========================
# EXECUTION
# =========================
for id in "${CHUNK_IDS[@]}"; do
    # COMMENT: Since it appears that command as string and the use of bash .. bash.. is bad design,
    # it was the only way i found to be able to manage the use of \"\" and other operators like > < etc. 

    START=$((id * CHUNK_SIZE))
    CHUNK_FILES=( "${FILES[@]:$START:$CHUNK_SIZE}" )

    # replace placeholder with current chunk id
    ARGS_FILLED="${ARGS//__TASK_ID__/$id}"

    BASE_CMD=(bash run_cmd_on_files.sh \"$COMMAND\" \"$ARGS_FILLED\" \"$CONDA_ENV\" ${CHUNK_FILES[@]})

    # create execution script for this chunk
    EXEC_FILE="$RUN_DIR/job_$id.sh"
    echo "#!/bin/bash" > "$EXEC_FILE"
    echo "${BASE_CMD[@]}" >> "$EXEC_FILE"
    chmod +x "$EXEC_FILE"

    if [[ "$USE_SLURM" != true && "$USE_SCREEN" != true ]]; then
        # -------- DIRECT LOCAL MODE --------
        LOCAL_CMD="bash $EXEC_FILE > $RUN_DIR/job_$id.out 2> $RUN_DIR/job_$id.err"
        if [ "$DRY_RUN" = true ]; then
            echo ""
            echo "[DRY-RUN][LOCAL][chunk $id]"
            echo bash -c \"$LOCAL_CMD\"
            continue
        fi

        echo ""
        echo "Running locally: chunk $id"
        bash -c "$LOCAL_CMD"
    else 
        # -------- SLURM MODE --------
        if [ "$USE_SLURM" = true ]; then
            SBATCH_CMD=(sbatch --job-name=showers_$id --output=$RUN_DIR/job_$id.out --error=$RUN_DIR/job_$id.err --cpus-per-task=$CPUS $EXEC_FILE)

            if [ "$DRY_RUN" = true ]; then
                echo ""
                echo "[DRY-RUN][SLURM][chunk $id]"
                echo "${SBATCH_CMD[@]}"
                continue
            fi

            "${SBATCH_CMD[@]}"

        else
        # -------- LOCAL MODE + Screen --------
            SESSION="showers_$id"

            INNER_CMD="bash $EXEC_FILE > $RUN_DIR/job_$id.out 2> $RUN_DIR/job_$id.err"
            SCREEN_CMD=(screen -dmS $SESSION bash -c "$INNER_CMD")

            if [ "$DRY_RUN" = true ]; then
                echo ""
                echo "[DRY-RUN][SCREEN][chunk $id]"
                echo screen -dmS $SESSION bash -c \"$INNER_CMD\"
                continue
            fi

            echo ""
            echo "Starting screen session: $SESSION"
            "${SCREEN_CMD[@]}"
        fi
    fi
done