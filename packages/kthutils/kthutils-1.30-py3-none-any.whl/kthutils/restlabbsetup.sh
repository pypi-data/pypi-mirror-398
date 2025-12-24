kthutils config forms.rewriter.restlabb -s ""
kthutils config forms.rewriter.restlabb.format_string -s "
echo 'Time:         {time}'
echo 'Course:       {course}'
echo 'Module:       {module}'
echo 'Student:      {student}'
echo 'Comments:     {comments}'
echo 'Grader:       {grader}'
echo 'In Canvas:    {in_canvas}'
if [ '{in_canvas}' = 'Ja' ]; then
  echo 'Already in Canvas.'
else
  canvaslms grade \\
    -c '{course_nick}{year}' \\
    -a '{assignment}' \\
    -u '{student}' \\
    -g '{grade}' \\
    -m 'OK {grader}'
fi
echo 'Canvas:'
canvaslms submissions \\
  -c '{course_nick}{year}' \\
  -a '{assignment}' \\
  -u '{student}'
echo
canvaslms results \\
  -c '{course_nick}{year}' \\
  -A '{assignment_group}' \\
  -u '{student}' \\
| sed -E 's/ ?[HV]T[0-9]{{2}}( \(.*\))?//' \\
| ladok report -fv
echo
"
kthutils config forms.rewriter.restlabb.substitutions.time.column -s 0
kthutils config forms.rewriter.restlabb.substitutions.module.column -s 5
kthutils config forms.rewriter.restlabb.substitutions.comments.column -s 6
kthutils config forms.rewriter.restlabb.substitutions.course.column -s 3
kthutils config forms.rewriter.restlabb.substitutions.course_code.column -s 3
kthutils config forms.rewriter.restlabb.substitutions.course_code.regex \
  -s "s/^.*([A-Z]{2}\d{3,4}[A-Z]?).*$/\1/"
kthutils config forms.rewriter.restlabb.substitutions.semester.column -s 3
kthutils config forms.rewriter.restlabb.substitutions.semester.regex \
  -s "s/^.*[Hh][Tt](\d{2}).*$/HT\1/" \
  -s "s/^.*[Vv][Tt](\d{2}).*$/VT\1/"
kthutils config forms.rewriter.restlabb.substitutions.course_nick.column -s 3
kthutils config forms.rewriter.restlabb.substitutions.course_nick.regex \
  -s "s/^.*DD1310.*(CMAST|[SC]ITEH?)?.*$/prgm/" \
  -s "s/^.*DD1317.*(prgi)?.*$/prgi/"
kthutils config forms.rewriter.restlabb.substitutions.year.column -s 3
kthutils config forms.rewriter.restlabb.substitutions.year.regex \
  -s "s/^.*([HhVv][Tt][- ]*|prg[im])(?:20)?(\d{2}).*$/\2/"
kthutils config forms.rewriter.restlabb.substitutions.grader.column -s 11
kthutils config forms.rewriter.restlabb.substitutions.grader.regex \
  -s "s/^.*?([A-Za-z0-9]+@kth.se).* $/\1/"
kthutils config forms.rewriter.restlabb.substitutions.student.column -s 2
kthutils config forms.rewriter.restlabb.substitutions.student.regex \
  -s "s/^.*?([A-Za-z0-9]+@kth.se).*$/\1/"
kthutils config forms.rewriter.restlabb.substitutions.in_canvas.column -s 7
kthutils config forms.rewriter.restlabb.substitutions.grade.column -s 5
kthutils config forms.rewriter.restlabb.substitutions.grade.regex \
  -s "s/.*([Bb]etyg|,)?\b([A-F])(\b.*)?$/\2/" \
  -s "s/.*(EJ GODKÄN[TD]|[Ee]j godkän[dt]).*$/F/"
kthutils config forms.rewriter.restlabb.substitutions.grade.no_match_default \
  -s P
kthutils config forms.rewriter.restlabb.substitutions.assignment.column -s 5
kthutils config forms.rewriter.restlabb.substitutions.assignment.regex \
  -s 's/.*[Pp](.?[Uu]ppgift|rojekt)[s ]?(?![sg]).*/redovisning/' \
  -s 's/.*[Ss][Pp][Ee][Cc].*/spec/' \
  -s 's/.*[Gg](ransk|RANSK).*/granskning/' \
  -s 's/.*[Ll]ab(?:b|oration)? *(\d-\d)\D*.*/Laboration..[\1]./' \
  -s 's/.*[Ll]ab(?:b|oration)? *(\d+(?:\s*(?:[,&+]| och | å )\s*\d+)*)\D*.*/Laboration .(\1)./; s/(?<=\d)\s*(?:[,&+]| och | å )\s*(?=\d)/|/'
kthutils config forms.rewriter.restlabb.substitutions.assignment_group.column -s 5
kthutils config forms.rewriter.restlabb.substitutions.assignment_group.regex \
  -s "s/.*[Ll]ab(b|oration).*/LAB1/" \
  -s "s/.*[Pp]-?(upp(gift)?|UPP(GIFT)?|rojekt|ROJEKT).*/LAB3/" \
  -s "s/.*[Ss][Pp][Ee][Cc].*/LAB3/" \
  -s "s/.*[Gg](ransk|RANSK).*/LAB3/" \
  -s "s/.*[Rr](edovisn|EDOVISN).*/LAB3/"
