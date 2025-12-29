\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{autoprob}[2025/12/26]

\newif\ifshowsolutions
\showsolutionsfalse
\newif\ifshowanswers
\showanswersfalse
\newif\ifgivespace
\givespacefalse

\DeclareOption{solutions}{\showsolutionstrue}
\DeclareOption{answers}{\showanswerstrue}
\DeclareOption{givespace}{\givespacetrue}

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

\LoadClass{article}

% core
\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage[margin=1in]{geometry}
\RequirePackage{calc}

% math
\RequirePackage{amsmath}
\RequirePackage{amssymb}
\RequirePackage{amsfonts}
\RequirePackage{amstext}
\RequirePackage{mathtools}
\RequirePackage{latexsym}
\RequirePackage[mathscr]{euscript}
\RequirePackage{nccmath}
\RequirePackage{accents}
\RequirePackage[version=4]{mhchem}

% utilities
\RequirePackage{xifthen}
\RequirePackage{xfp}
\RequirePackage{currfile}
\RequirePackage{datatool}
\RequirePackage{soul}

% tables
\RequirePackage{array}
\RequirePackage{multirow}
\RequirePackage{longtable}
\RequirePackage{booktabs}
\RequirePackage[font=small,labelfont=bf]{caption}

% graphics / code
\RequirePackage{tikz}
\RequirePackage{listings}
\RequirePackage{pythontex}

% lists / headers
\RequirePackage{enumitem}
\RequirePackage{fancyhdr}

% hyperlinks LAST
\RequirePackage{hyperref}

\usetikzlibrary{patterns}



\newsavebox{\fmbox}
\newenvironment{fmpage}[1]
{\begin{lrbox}{\fmbox}\begin{minipage}[c]{#1}}
{\end{minipage}\end{lrbox}\fbox{\usebox{\fmbox}}}

\definecolor{Brown}{cmyk}{0,0.81,1,0.60}
\definecolor{OliveGreen}{cmyk}{0.64,0,0.95,0.40}
\definecolor{CadetBlue}{cmyk}{0.62,0.57,0.23,0}
\definecolor{lightlightgray}{gray}{0.9}
\lstdefinestyle{mybash}{language=bash,basicstyle=\ttfamily\color{white},backgroundcolor=\color{black},numbers=none,keywordstyle=\bf\color{white},showspaces=false,showstringspaces=false}
\lstdefinestyle{myc}{language=C,basicstyle=\ttfamily\color{CadetBlue},backgroundcolor=\color{lightlightgray},frame=none,numbers=none,keywordstyle=\bf\color{CadetBlue},tabsize=2,showspaces=false,showstringspaces=false}
\lstdefinestyle{mypython}{
language=Python,                             % Code langugage
basicstyle=\footnotesize\ttfamily,                   % Code font, Examples: \footnotesize, \ttfamily
keywordstyle=\color{OliveGreen},        % Keywords font ('*' = uppercase)
commentstyle=\color{gray},              % Comments font
numbers=left,                           % Line nums position
numberstyle=\tiny,                      % Line-numbers fonts
stepnumber=1,                           % Step between two line-numbers
numbersep=5pt,                          % How far are line-numbers from code
backgroundcolor=\color{lightlightgray}, % Choose background color
frame=none,                             % A frame around the code
tabsize=4,                              % Default tab size
captionpos=b,                           % Caption-position = bottom
breaklines=true,                        % Automatic line breaking?
breakatwhitespace=false,                % Automatic breaks only at whitespace?
showspaces=false,                       % Dont make spaces visible
showstringspaces=false,
showtabs=false,                         % Dont make tabls visible
numbers=none
%columns=flexible,                       % Column format
}
\newcommand{\inl}[1][]{%
  \lstinline[style=mypython,basicstyle=\ttfamily,#1]%
}

\DeclareRobustCommand{\molar}[1]{\protect\underaccent{\bar}{#1}}
\newcommand{\parmol}[2]{\overline{#1}_{#2}}
\def\Ub{\molar{U}}
\def\Hb{\molar{H}}
\def\Sb{\molar{S}}
\def\Vb{\molar{V}}
\def\Gb{\molar{G}}
\def\thetab{\molar{\theta}}
\newcommand{\dm}[1]{\Delta_{\rm mix} {#1}}
\newcommand{\deriv}[2]{\frac{d{#1}}{d{#2}}}
\newcommand{\pv}{P^{\rm vap}}
\newcommand{\pd}[2]{\frac{\partial {#1}}{\partial {#2}}}
\newcommand{\tpd}[3]{\left(\frac{\partial {#1}}{\partial {#2}}\right)_{#3}}
\newcommand{\ppd}[2]{\frac{\partial^2 {#1}}{\partial {#2}^2}}
\newcommand{\dr}[1]{\Delta_{\rm rxn} {#1}}
\newcommand{\df}[1]{\Delta_{\rm f} {#1}^\circ}
\newcommand{\hr}{\dr{H^{\circ}}}
\newcommand{\gr}{\dr{G^{\circ}}}
\newcommand{\hf}{\df{H}}
\newcommand{\gf}{\df{G}}

\newcommand{\tffillblank}{\ul{\ \ \ \ \ \ }}
\newcommand{\tfitem}[2]{\item[{{#1}}. \ifshowsolutions\textcolor{blue}{\underline{{#2}}}\else\tffillblank\fi]}
\newcommand{\fitbfillblank}{\ul{\ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ \ }}
\newcommand{\fitanswerslot}[1]{\ifshowsolutions\textcolor{blue}{\underline{{#1}}}\else\fitbfillblank\fi}
\newcommand{\mcchoiceitem}[2]{\item[\ifshowsolutions\ifthenelse{\equal{{#1}}{{#2}}}{\textcolor{blue}{\fbox{\textbf{#1}}}}{#1}\else #1\fi.]}

\newcommand{\Universityname}{\so{\sc University Name}}
\newcommand{\Departmentname}{Department Name}
\newcommand{\Coursename}{Course Name}
\newcommand{\Termname}{Term Name}
\newcommand{\Termcode}{Term Code}
\newcommand{\Instructorname}{Instructor Name}
\newcommand{\Instructoremail}{instructor@example.com}
\newcommand{\Subjectname}{Subject Name}

\newcommand{\Solutionscolor}{blue}
\newcommand{\Solutionstitle}{\color{\Solutionscolor}\so{\sc SOLUTIONS}\color{black}}
\newcommand{\Solutionheader}{\color{\Solutionscolor}{\sc SOLUTION}\color{black}}

\newcommand{\plainheader}[1]{
    \begin{centering}
        \Universityname\\
        \Departmentname\\
        \Coursename\ -- \Termname\ (\Termcode)\\*[0.5em]
        {#1}\\
    \end{centering}
}

\newcommand{\asnheader}[2]{
    \begin{centering}
        {\sc \Universityname}\\
        \Departmentname\\
        \Coursename\ -- \Termname\ (\Termcode)\\
        \Instructorname\\
        {\sc {#1}\ }\\
        Due {#2}\\*[1em]
        \ifshowsolutions
        \Solutionstitle\\*[1em]
        \fi
    \end{centering}
}

\newcommand{\examheader}[2]{
    \begin{centering}
        \Universityname\\
        \Departmentname\\
        \Coursename\\
        \Termname\ (\Termcode)\\
        \Instructorname\ -- \Instructoremail\\
        {#1}\ -- {#2}\\*[1em]
        \ifshowsolutions
        \Solutionstitle\\*[2em]
        \fi
    \end{centering}
}

\newcommand{\qualifierheader}[1]{
    \begin{centering}
        \Universityname\\
        \Departmentname\\
        Ph.D. Qualifying Exam\\
        \Subjectname\\
        {#1}\\*[5mm]
        \ifshowsolutions
        \Solutionstitle\\*[1cm]
        \fi
    \end{centering}
}

\newcommand{\morespace}[1]{
\noindent More space for problem #1
\clearpage
}
\newcommand\examquestion[2]{\givespacetrue\newcommand\totalpoints{#1}\input{#2}\givespacefalse}
\newcommand\qualquestion[2]{\input{#1}\ifgivespace\morespace{#2}\fi}
\newcommand\practicequestion[1]{\givespacefalse\input{#1}}
\newcommand\problem[1]{\input{#1}}


\newlength{\hght}
\newlength{\wdth}

\newcommand{\cancelto}[3][.5ex]{\setlength{\hght}{\heightof{$#3$}}\setlength{\wdth}{\widthof{$#3$}}%
    \makebox[0pt][l]{\tikz[baseline]{\draw[-latex](0,-#1)--(\wdth,\hght+#1) node[shift={(1mm,.5mm)}]{#2};}}#3}
