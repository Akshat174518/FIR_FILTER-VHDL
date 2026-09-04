library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.textio.all;

entity fir_filter_tb is
end entity fir_filter_tb;

architecture sim of fir_filter_tb is

  constant DATA_WIDTH  : integer := 16;
  constant CLK_PERIOD  : time    := 10 ns;

  signal clk       : std_logic := '0';
  signal rst_n     : std_logic := '0';
  signal data_in   : std_logic_vector(DATA_WIDTH-1 downto 0) := (others => '0');
  signal valid_in  : std_logic := '0';
  signal data_out  : std_logic_vector(DATA_WIDTH-1 downto 0);
  signal valid_out : std_logic;

  signal sim_done  : boolean := false;

  file stim_file : text open read_mode is "data/stimulus.txt";
  file exp_file  : text open read_mode is "data/expected_output.txt";

begin

  dut : entity work.fir_filter
    generic map (
      NUM_TAPS    => 16,
      DATA_WIDTH  => 16,
      COEFF_WIDTH => 16,
      ACC_WIDTH   => 40
    )
    port map (
      clk       => clk,
      rst_n     => rst_n,
      data_in   => data_in,
      valid_in  => valid_in,
      data_out  => data_out,
      valid_out => valid_out
    );

  -- Clock
  clk_gen : process
  begin
    while not sim_done loop
      clk <= '0'; wait for CLK_PERIOD / 2;
      clk <= '1'; wait for CLK_PERIOD / 2;
    end loop;
    wait;
  end process;

  -- Reset
  rst_proc : process
  begin
    rst_n <= '0';
    wait for CLK_PERIOD * 4;
    rst_n <= '1';
    wait;
  end process;

  -- Drive stimulus, one sample per cycle, after reset deasserts
  stim_proc : process
    variable l    : line;
    variable ival : integer;
  begin
    valid_in <= '0';
    wait until rst_n = '1';
    wait until rising_edge(clk);

    while not endfile(stim_file) loop
      readline(stim_file, l);
      read(l, ival);
      data_in  <= std_logic_vector(to_signed(ival, DATA_WIDTH));
      valid_in <= '1';
      wait until rising_edge(clk);
    end loop;

    valid_in <= '0';
    wait;
  end process;

  -- Check every valid output against the golden model
  check_proc : process
    variable l          : line;
    variable expected   : integer;
    variable actual     : integer;
    variable pass_count : integer := 0;
    variable fail_count : integer := 0;
  begin
    wait until rst_n = '1';

    while not endfile(exp_file) loop
      wait until rising_edge(clk);
      if valid_out = '1' then
        readline(exp_file, l);
        read(l, expected);
        actual := to_integer(signed(data_out));

        if actual = expected then
          pass_count := pass_count + 1;
        else
          fail_count := fail_count + 1;
          report "MISMATCH at sample " & integer'image(pass_count + fail_count) &
                 ": expected " & integer'image(expected) &
                 ", got " & integer'image(actual)
            severity warning;
        end if;
      end if;
    end loop;

    report "----------------------------------------------------";
    report "FIR filter testbench complete: " &
           integer'image(pass_count) & " passed, " &
           integer'image(fail_count) & " failed";
    report "----------------------------------------------------";

    if fail_count = 0 then
      report "RESULT: PASS" severity note;
    else
      report "RESULT: FAIL" severity error;
    end if;

    sim_done <= true;
    wait;
  end process;

end architecture sim;
