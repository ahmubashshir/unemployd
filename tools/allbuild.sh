#!/bin/bash
# ppc64,ppc64le
# mips64le,mips64,
declare -A config
while IFS=$'\t' read -r key value; do
	config["${key#linux/}"]="$value"
done < <(
	./tools/arch/matrix \
		| sed -nE 's/^matrix=//p' \
		| jq -r '.include | map([.platform, .builder] | join("\t")) | join("\n")'
)

platforms=(
	386
	arm64
	arm/v6
	arm/v7
	ppc64le
	riscv64
	s390x
	loong64
	amd64
)
./tools/arch/matrix \
	| sed -nE '
	/^targets<<EOF$/,/^EOF$/{
		/^EOF$/d
		/^targets<<EOF$/s/^.+$/Platforms:/
		s@^linux-@  @
		s@-@/@g
		p
	}' >&2

#for pf in "${platforms[@]}"; do
#	[[ ${config["$pf"]} ]] || {
#		echo "Unsupported platform: $pf" >&2
#		continue
#	}
#
#	printf '================ %s ==============\n' "$pf"
#	podman build \
#		-o "type=local,dest=./outputs/${pf//\//-}" \
#		--platform "linux/$pf" \
#		--build-arg builder="${config["$pf"]}" \
#		-t "${PWD##*/}:${pf//\//-}" .
#done
#

# Collect supported platforms.
jobs=()
for pf in "${platforms[@]}"; do
	if [[ ${config["$pf"]:-} ]]; then
		jobs+=("$pf")
	else
		echo "Unsupported platform: $pf" >&2
	fi
done

if ((${#jobs[@]} == 0)); then
	echo "No supported platforms." >&2
	exit 1
fi
# Generate a worker script with its own configuration.
BUILD_SCRIPT=$(
	{
		declare -p config
		declare -p jobs

		cat << 'WORKER'
wait() {
	local _
	read -rsp "$1" _
	echo
} >&2

set -u
worker_id="$1"
max_jobs="$2"
logdir="$3"
project_dir="$4"

cd "$project_dir" || {
	echo "CD to $project_dir faild.";
	wait 'Press RETURN to close this pane...'
	exit 1;
}

for ((i = worker_id; i < ${#jobs[@]}; i += max_jobs))
do
	pf="${jobs[$i]}"
	name="${pf//\//-}"
	logfile="$logdir/$name.log"

	echo "================ $pf ================"

	podman build \
		-o "type=local,dest=./outputs/$name" \
		--platform "linux/$pf" \
		--build-arg "builder=${config[$pf]}" \
		-t "${PWD##*/}:$name" . 2>&1 # | tee "$logfile"

	rc=${PIPESTATUS[0]}
	echo "Build $pf exited with status $rc"
done

echo "Worker $worker_id finished.";
wait 'Press Enter to close this pane...'
WORKER
	}
)

# One pane per worker, capped at max_jobs.
worker_count=$(($( nproc) / 2))
((worker_count < 1)) && worker_count=1
((worker_count > ${#jobs[@]})) && worker_count=${#jobs[@]}

session="arch-build"
logdir="$PWD/outputs/logs"
mkdir -p "$logdir"

if tmux has-session -t "$session" 2> /dev/null; then
	echo "Session '$session' already exists." >&2
	exit 1
fi

project_dir="$PWD"
tmux new-session -d -s "$session" -n builds \
	-c "$project_dir" sleep infinity

for ((w = 0; w < worker_count; w++)); do
	if ((w == 0)); then
		pane_id=$(tmux display-message -p -t "$session" '#{pane_id}')
	else
		pane_id=$(tmux split-window -d -P -F '#{pane_id}' \
			-t "$session" -c "$project_dir" sleep infinity) || exit 1
	fi

	tmux select-layout -t "$session" tiled
	tmux respawn-pane -k -t "$pane_id" \
		bash -c "$BUILD_SCRIPT" "worker-$w" \
		"$w" "$worker_count" "$logdir" "$project_dir"
done

echo "CPUs: $(nproc)"
echo "Concurrency: $worker_count"
echo "Platforms: ${#jobs[@]}"
echo "Logs: $logdir"
echo "Attach: tmux attach -t $session"

tmux attach -t "$session"
