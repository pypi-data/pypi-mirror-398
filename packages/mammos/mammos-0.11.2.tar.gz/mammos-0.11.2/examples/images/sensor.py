import pathlib
import mochada_kit as mk
from mochada_kit.running import run_plantuml_code

themes_dir = mk._THEMES_DIR

puml_code = f"""@startuml
!theme MOCHADA-CWA from {themes_dir}

:Select a material; <<user_case_input>>
group mammos-spindynamics <<group_single>>
  :Load from SD database; <<data_based_model>>
  :Temperature‐dependent Ms(T); <<raw_output>>
end group

group mammos-analysis <<group_single>>
  :Use Kuzmin model; <<model>>
  :Temperature‐dependent <i>M</i><sub>s</sub>(<i>T</i>), <i>A</i>(<i>T</i>); <<raw_output>>
end group

:Select a working temperature (T); <<user_case_input>>

'  Build & run the micromagnetic model
group optimization <<group_single>>
repeat
    :Propose new geometry; <<user_case_input>>
    group ubermag <<group_single>>
      :Run micromagnetic simulation; <<model>>
      :Output hysteresis loops; <<raw_output>>
    end group
    '  Post‐processing

    group mammos-analysis <<group_single>>
      :Extract linear segment from loops; <<processed_output>>
    end group
repeat while
end group

:Optimal geometry; <<processed_output>>

@enduml
"""

puml_path = pathlib.Path("sensor_workflow.puml")
puml_path.write_text(puml_code, encoding="utf-8")

run_plantuml_code(
    puml_path,
    output_dir=pathlib.Path("."),
)
