/**
 * export CLASSPATH=".:/usr/local/lib/antlr-4.13.2-complete.jar:$CLASSPATH"
 * alias antlr4='java -jar /usr/local/lib/antlr-4.13.2-complete.jar'
 * alias grun='java org.antlr.v4.runtime.misc.TestRig'
 * cd /mnt/d/gitwork/nextnextping/nextnextping/grammer/
 * antlr4 -visitor -Dlanguage=Python3 ttl_parser.g4
 */
grammar ttl_parser;


NUMBER: [-+]? [0-9]+;
NUMBER_16: '$' [-+]? [a-fA-F0-9]+;

//NUMBER_ASCII: '#' '$'? [a-fA-F0-9]+;
//STRING1: '\'' ~[']* '\'';
//STRING2: '"' ~["]* '"';
//strContext: (STRING1 | STRING2 | NUMBER_ASCII)+;
STRING1: ('\'' ~[']* '\'' | '"' ~["]* '"' | '#' '$'? [a-fA-F0-9]+)+;
strContext: STRING1;


KEYWORD: [_a-zA-Z][_a-zA-Z0-9]*;
keyword: KEYWORD (LEFT_KAKKO (intExpression| strExpression) RIGHT_KAKKO)?;
LEFT_KAKKO: '[';
RIGHT_KAKKO: ']';

strExpression: strContext| keyword;

intContext
    : NUMBER
    | NUMBER_16
    ;
intExpression: intContext | keyword | '(' p11Expression ')';

p1Expression
    : intExpression
    | 'not' intExpression
    | '~' intExpression
    | '!' intExpression
    ;

p2Expression
    : p1Expression
    | p2Expression '*' p1Expression
    | p2Expression '/' p1Expression
    | p2Expression '%' p1Expression
    ;

p3Expression
    : p2Expression
    | p3Expression '+' p2Expression
    | p3Expression '-' p2Expression
    ;

p4Expression
    : p3Expression
    | p4Expression '>>>' p3Expression
    | p4Expression '>>' p3Expression
    | p4Expression '<<' p3Expression
    ;

p5Expression
    : p4Expression
    | p5Expression 'and' p4Expression
    | p5Expression '&' p4Expression
    ;

p6Expression
    : p5Expression
    | p6Expression 'xor' p5Expression
    | p6Expression '^' p5Expression
    ;

p7Expression
    : p6Expression
    | p7Expression 'or' p6Expression
    | p7Expression '|' p6Expression
    ;

p8Expression
    : p7Expression
    | p8Expression '<' p7Expression
    | p8Expression '>' p7Expression
    | p8Expression '<=' p7Expression
    | p8Expression '>=' p7Expression
    ;

p9Expression
    : p8Expression
    | p9Expression '=' p8Expression
    | p9Expression '==' p8Expression
    | p9Expression '<>' p8Expression
    | p9Expression '!=' p8Expression
    ;

p10Expression
    : p9Expression
    | p10Expression '&&' p9Expression
    ;

p11Expression
    : p10Expression
    | p11Expression '||' p10Expression
    ;

RN: '\r'? '\n'
    | ';' ~[\n]* '\n'
    ;

WS1 : [ \t]+ -> skip;
WS2 : '/*' ~[/]* '*/'-> skip;


command
    : 'bplusrecv'
    | 'bplussend' strExpression
    | 'callmenu' p11Expression
    | 'changedir' strExpression
    | 'clearscreen' strExpression
    | 'closett' 
    | 'connect' strExpression
    | 'cygconnect' strExpression?
    | 'disconnect'
    | 'dispstr' strExpression+
    | 'enablekeyb' p11Expression
    | 'flushrecv' 
    | 'gethostname' keyword
    | 'getmodemstatus' keyword
    | 'gettitle' keyword
    | 'getttpos' p11Expression p11Expression p11Expression p11Expression p11Expression p11Expression p11Expression p11Expression p11Expression
    | 'kmtfinish'
    | 'kmtget' strExpression
    | 'kmtrecv'
    | 'kmtsend' strExpression
    | 'loadkeymap' strExpression
    | 'logautoclosemode' p11Expression
    | 'logclose'
    | 'loginfo' strExpression
    | 'logopen' strExpression p11Expression+
    | 'logpause'
    | 'logrotate' strExpression p11Expression p11Expression (p11Expression (p11Expression (p11Expression (p11Expression p11Expression?) ?) ? )? )?
    | 'logstart' 
    | 'logwrite' strExpression
    | 'quickvanrecv'
    | 'quickvansend' strExpression
    | 'recvln'
    | 'restoresetup' strExpression
    | 'scprecv' strExpression strExpression?
    | 'scpsend' strExpression strExpression?
    | 'send' strExpression+
    | 'sendbinary' (strExpression|p11Expression)+
    | 'sendbreak'
    | 'sendbroadcast' (strExpression|p11Expression)+
    | 'sendfile' strExpression p11Expression
    | 'sendkcode' p11Expression p11Expression
    | 'sendln' strExpression*
    | 'sendlnbroadcast' strExpression*
    | 'sendlnmulticast' strExpression (strExpression|p11Expression)+
    | 'sendtext' (strExpression|p11Expression)+
    | 'sendmulticast' strExpression (strExpression|p11Expression)+
    | 'setbaud' p11Expression
    | 'setdebug' p11Expression
    | 'setdtr' p11Expression
    | 'setecho' p11Expression
    | 'setflowctrl' p11Expression
    | 'setmulticastname' strExpression
    | 'setrts' p11Expression
    | 'setserialdelaychar' p11Expression
    | 'setserialdelayline' p11Expression
    | 'setspeed' p11Expression
    | 'setsync' p11Expression
    | 'settitle' strExpression
    | 'showtt' p11Expression
    | 'testlink'
    | 'unlink'
    | 'wait' strExpression+
    | 'wait4all' strExpression+
    | 'waitevent' p11Expression
    | 'waitln' strExpression+
    | 'waitn' p11Expression
    | 'waitrecv' strExpression p11Expression p11Expression
    | 'waitregex' strExpression+
    | 'xmodemrecv' strExpression p11Expression p11Expression
    | 'xmodemsend' strExpression p11Expression
    | 'ymodemrecv'
    | 'ymodemsend' strExpression
    | 'zmodemrecv' 
    | 'zmodemsend' strExpression p11Expression

    | 'break'
    | 'call' KEYWORD
    | 'continue'
    | 'end'
    | 'execcmnd' strExpression
    | 'exit'
    | 'goto' strExpression
    | 'include' strExpression
    | 'mpause' p11Expression
    | 'pause' p11Expression
    | 'return'

    | 'code2str' keyword p11Expression
    | 'expandenv' keyword strExpression?
    | 'int2str' keyword p11Expression
    | 'regexoption' strExpression+
    | 'sprintf' strExpression (strExpression|p11Expression)*
    | 'sprintf2' keyword strExpression (strExpression|p11Expression)*
    | 'str2code' keyword strExpression
    | 'str2int' keyword strExpression
    | 'strcompare' strExpression strExpression
    | 'strconcat' keyword strExpression
    | 'strcopy' strExpression p11Expression p11Expression keyword
    | 'strinsert' keyword p11Expression strExpression
    | 'strjoin' keyword strExpression p11Expression?
    | 'strlen' strExpression
    | 'strmatch' strExpression strExpression
    | 'strremove' keyword p11Expression p11Expression
    | 'strreplace' keyword p11Expression strExpression strExpression
    | 'strscan' strExpression strExpression
    | 'strspecial' keyword strExpression?
    | 'strsplit' keyword strExpression p11Expression?
    | 'strtrim' keyword strExpression
    | 'tolower' keyword strExpression
    | 'toupper' keyword strExpression
    | 'basename' keyword strExpression
    | 'dirname' keyword strExpression
    | 'fileclose' keyword
    | 'fileconcat' strExpression strExpression
    | 'filecopy' strExpression strExpression
    | 'filecreate' keyword strExpression
    | 'filedelete' strExpression
    | 'filelock' keyword p11Expression?
    | 'filemarkptr' keyword
    | 'fileopen' keyword strExpression p11Expression p11Expression?
    | 'filereadln' keyword keyword
    | 'fileread' keyword p11Expression keyword
    | 'filerename' strExpression strExpression
    | 'filesearch' strExpression
    | 'fileseek' keyword strExpression
    | 'fileseekback' keyword
    | 'filestat' strExpression keyword (keyword keyword?)?
    | 'filestrseek' keyword strExpression
    | 'filestrseek2' keyword strExpression
    | 'filetruncate' strExpression p11Expression
    | 'fileunlock' keyword
    | 'filewrite' keyword (strExpression|p11Expression)*
    | 'filewriteln' keyword (strExpression|p11Expression)*
    | 'findfirst' keyword strExpression keyword
    | 'findnext' keyword keyword
    | 'findclose' keyword
    | 'foldercreate' strExpression
    | 'folderdelete' strExpression
    | 'foldersearch' strExpression
    | 'getdir' keyword
    | 'getfileattr' strExpression
    | 'makepath' keyword strExpression strExpression
    | 'setdir' strExpression
    | 'setfileattr' strExpression p11Expression
    | 'delpassword' strExpression strExpression
    | 'delpassword2' strExpression strExpression
    | 'getpassword' strExpression strExpression keyword
    | 'getpassword2' strExpression strExpression keyword p11Expression
    | 'ispassword' strExpression strExpression
    | 'ispassword2' strExpression strExpression
    | 'passwordbox' strExpression strExpression p11Expression?
    | 'setpassword' strExpression strExpression keyword
    | 'setpassword2' strExpression strExpression keyword strExpression

    | 'beep' p11Expression?
    | 'bringupbox'
    | 'checksum8' keyword strExpression
    | 'checksum8file' keyword strExpression
    | 'checksum16' keyword strExpression
    | 'checksum16file' keyword strExpression
    | 'checksum32' keyword strExpression
    | 'checksum32file' keyword strExpression
    | 'closesbox'
    | 'clipb2var' keyword p11Expression
    | 'crc16' keyword strExpression
    | 'crc16file' keyword strExpression
    | 'crc32' keyword strExpression
    | 'crc32file' keyword strExpression
    | 'exec' strExpression (strExpression (p11Expression strExpression?) ? )?
    | 'dirnamebox' strExpression p11Expression?
    | 'filenamebox' strExpression p11Expression? strExpression?
    | 'getdate' keyword (strExpression strExpression? )?
    | 'getenv' strExpression keyword
    | 'getipv4addr' keyword keyword
    | 'getipv6addr' keyword keyword
    | 'getspecialfolder' p11Expression strExpression
    | 'gettime' keyword strExpression? strExpression?
    | 'getttdir' keyword
    | 'getver' keyword strExpression?
    | 'ifdefined' KEYWORD
    | 'inputbox' strExpression strExpression strExpression? p11Expression?
    | 'intdim' KEYWORD p11Expression
    | 'listbox' strExpression strExpression keyword p11Expression? strExpression*
    | 'messagebox' strExpression strExpression p11Expression?
    | 'random' keyword p11Expression
    | 'rotateleft' keyword p11Expression p11Expression
    | 'rotateright' keyword p11Expression p11Expression
    | 'setdate' strExpression
    | 'setdlgpos' p11Expression*
    | 'setenv' strExpression keyword
    | 'setexitcode' p11Expression
    | 'settime' strExpression
    | 'show' p11Expression
    | 'statusbox' strExpression strExpression p11Expression?
    | 'strdim' KEYWORD p11Expression
    | 'uptime' keyword
    | 'var2clipb' strExpression
    | 'yesnobox' strExpression strExpression p11Expression?
    | 'assert' p11Expression (strExpression|p11Expression)*
    ;

forNext
    : 'for' keyword p11Expression p11Expression RN commandline+ 'next';

whileEndwhile
    : 'while' p11Expression RN commandline+ 'endwhile';

untilEnduntil
    : 'until' p11Expression RN commandline+ 'enduntil';

doLoop
    : 'do' p11Expression? RN commandline+ 'loop' p11Expression?;

if1
    : 'if' p11Expression commandline;

if2
    : 'if' p11Expression 'then' RN commandline+ (elseif)* (else)? 'endif';

elseif:'elseif' p11Expression 'then' RN commandline+;

else: 'else' RN commandline+;

input: keyword '=' (strExpression | p11Expression);

label: ':' KEYWORD ;

commandline
    : input RN
    | if2
    | if1
    | forNext RN
    | whileEndwhile RN
    | label RN
    | command RN
    | untilEnduntil RN
    | doLoop RN
    | RN
    ;

statement: commandline+ EOF;


/*  */
