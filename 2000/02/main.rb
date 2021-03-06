require 'aoc_executor'

part1_proc = Proc.new { |input| "Hello" }
part2_proc = Proc.new { |input| "World" }
executor = AocExecutor.new(%w[], part1_proc, part2_proc)
executor.run(ARGV)
