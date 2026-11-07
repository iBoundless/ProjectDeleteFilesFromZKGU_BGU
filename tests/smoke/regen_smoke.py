import io
ROOT="/srv/projects/ProjectDeleteFilesFromZKGU_BGU/src/СозданиеАрхиваДокументооборота"
auto=io.open("/tmp/opencode/epf/autotest.bsl",encoding="utf-8").read()
src=io.open(ROOT+"/Forms/ВсеФайлы/Ext/Form/Module.bsl",encoding="utf-8-sig").read()
form=io.open(ROOT+"/Forms/ВсеФайлы/Ext/Form.xml",encoding="utf-8-sig").read()
form=form.replace('<Event name="OnCreateAtServer">ПриСозданииНаСервере</Event>',
                  '<Event name="OnCreateAtServer">ПриСозданииНаСервере</Event>\n\t\t<Event name="OnOpen">ПриОткрытии</Event>')
for base in ["smoke_src","smoke_src_bgu"]:
    mod = src
    mod = mod + auto
    if base=="smoke_src_bgu":
        mod = mod.replace("ФизическиеЛица","Организации").replace("Физлицо","Организация")
    io.open(f"/tmp/opencode/epf/{base}/СозданиеАрхиваДокументооборота/Forms/ВсеФайлы/Ext/Form/Module.bsl","w",encoding="utf-8").write(mod)
    io.open(f"/tmp/opencode/epf/{base}/СозданиеАрхиваДокументооборота/Forms/ВсеФайлы/Ext/Form.xml","w",encoding="utf-8").write(form)
    print(base,"ok")
