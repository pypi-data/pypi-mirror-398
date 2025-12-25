import pathlib
import mochada_kit as mk
from mochada_kit.running import run_plantuml_code

themes_dir = mk._THEMES_DIR

puml_code = f"""@startuml
!theme MOCHADA-CWA from {themes_dir}
split
  -[hidden]->
  split
    -[hidden]->
    :Select a material; <<user_case_input>>
    split
      group mammos-dft <<group_single>>
        :Load from DFT database; <<data_based_model>>
        :Zero temperature <i>M</i><sub>s</sub> & <i>K</i>; <<raw_output>>
      end group
    split again
      group mammos-spindynamics <<group_single>>
        :Load from SD database; <<data_based_model>>
        :Temperature‐dependent <i>M</i><sub>s</sub>(<i>T</i>); <<raw_output>>
      end group
    end split

    group mammos-analysis <<group_single>>
      :Use Kuzmin model; <<model>>
      :Temperature‐dependent <i>M</i><sub>s</sub>(<i>T</i>), <i>K</i>(<i>T</i>), <i>A</i>(<i>T</i>); <<raw_output>>
    end group
  split again
    -[hidden]->
    :Select a working temperature (T); <<user_case_input>>
  end split
  :Evaluate <i>M</i><sub>s</sub>(<i>T</i>), <i>K</i>(<i>T</i>), <i>A</i>(<i>T</i>) at the working temperature; <<output_processing>>
  :<i>M</i><sub>s</sub>, <i>K</i>, <i>A</i> at temperature T; <<processed_output>>
  '  Build & run the micromagnetic model
split again
  -[hidden]->
  :Select a microstructure and other\n micromagnetic input parameters; <<user_case_input>>
split end

group mammos-mumag <<group_single>>
  :Run micromagnetic simulation; <<model>>
  :Hysteresis loop; <<raw_output>>
end group
'  Post‐processing

group mammos-analysis <<group_single>>
  :Extract extrinsic properties; <<data_based_model>>
  :Hc, Mr, BHmax; <<raw_output>>
end group

@enduml
"""

puml_path = pathlib.Path("hard_magnet_workflow.puml")
puml_path.write_text(puml_code, encoding="utf-8")

run_plantuml_code(
    puml_path,
    output_dir=pathlib.Path("."),
)
