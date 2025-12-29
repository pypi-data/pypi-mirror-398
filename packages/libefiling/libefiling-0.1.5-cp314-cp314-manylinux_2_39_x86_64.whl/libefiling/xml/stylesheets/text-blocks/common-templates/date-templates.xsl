<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp">

    <!-- 
        日付処理関連のテンプレート
    -->

    <!-- ====================================================================
       元号・和暦年変換用 変数定義
       ====================================================================-->
    <!--begin
    令和 at the date. -->
    <xsl:variable name="date-r" select="20190501" />
    <!-- 2018 -> 令和0年 -->
    <xsl:variable name="year-r0" select="2018" />

    <!--begin
    平成 at the date-->
    <xsl:variable name="date-h" select="19890108" />
    <xsl:variable name="year-h0" select="1988" />

    <!--begin
    昭和 at the date-->
    <xsl:variable name="date-s" select="19261225" />
    <xsl:variable name="year-s0" select="1925" />

    <!--begin
    大正 at the date-->
    <xsl:variable name="date-t" select="19120730" />
    <xsl:variable name="year-t0" select="1911" />

    <!--begin
    明治 at the date-->
    <xsl:variable name="date-m" select="18680908" />
    <xsl:variable name="year-m0" select="1867" />

    <!-- ====================================================================
       和暦日付編集
         input: xs:string date "YYYYMMDD"
         output: 令和NN年MM月DD日
       ====================================================================-->
    <xsl:template name="format-date-jp">
        <xsl:param name="date-str" as="xs:string" />
        <xsl:variable name="m" select="substring($date-str,5,2)" />
        <xsl:variable name="d" select="substring($date-str,7,2)" />

        <xsl:choose>
            <xsl:when test="string-length($date-str) != 8" />
            <xsl:when test="number($date-str) &lt; 19260101" />
            <xsl:otherwise>
                <xsl:call-template name="gengo">
                    <xsl:with-param name="date" select="$date-str" />
                </xsl:call-template>
                <xsl:call-template name="warekinen">
                    <xsl:with-param name="date" select="$date-str" />
                </xsl:call-template>
                <xsl:value-of select="'年'" />
                <xsl:value-of select="$m || '月'" />
                <xsl:value-of select="$d || '日'" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- ====================================================================
       元号編集
       input: xs:string date "YYYYMMDD"
       output: 令和|平成|昭和|大正|明治
       ====================================================================-->
    <xsl:template name="gengo">
        <xsl:param name="date" as="xs:string" />
        <xsl:variable name="int-date" as="xs:integer">
            <xsl:choose>
                <xsl:when test="string-length($date) != 8">
                    <xsl:value-of select="-1" />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="xs:integer($date)" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="$int-date = -1" />
            <xsl:when test="$int-date &gt;= $date-r">
                <xsl:value-of select="'令和'" />
            </xsl:when>
            <xsl:when test="$int-date &gt;= $date-h">
                <xsl:value-of select="'平成'" />
            </xsl:when>
            <xsl:when test="$int-date &gt;= $date-s">
                <xsl:value-of select="'昭和'" />
            </xsl:when>
            <xsl:when test="$int-date &gt;= $date-t">
                <xsl:value-of select="'大正'" />
            </xsl:when>
            <xsl:when test="$int-date &gt;= $date-m">
                <xsl:value-of select="'明治'" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="'不明'" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- ====================================================================
       和暦年編集
         input: xs:string date "YYYYMMDD"
         output: NN
       ====================================================================-->
    <xsl:template name="warekinen">
        <xsl:param name="date" as="xs:string" />
        <xsl:variable name="int-date" as="xs:integer">
            <xsl:choose>
                <xsl:when test="string-length($date) != 8">
                    <xsl:value-of select="-1" />
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="xs:integer($date)" />
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="$int-date = -1" />
            <xsl:when test="$int-date &gt;= $date-r">
                <xsl:value-of select="floor($int-date div 10000) - $year-r0" />
            </xsl:when>
            <xsl:when test="$int-date &gt;= $date-h">
                <xsl:value-of select="floor($int-date div 10000) - $year-h0" />
            </xsl:when>
            <xsl:when test="$int-date &gt;= $date-s">
                <xsl:value-of select="floor($int-date div 10000) - $year-s0" />
            </xsl:when>
            <xsl:when test="$int-date &gt;= $date-t">
                <xsl:value-of select="floor($int-date div 10000) - $year-t0" />
            </xsl:when>
            <xsl:when test="$int-date &gt;= $date-m">
                <xsl:value-of select="floor($int-date div 10000) - $year-m0" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="'不明'" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>


    <!-- ====================================================================
         和暦変換
         application-reference//jp:doc-number のコンテキストで呼び出す。
         出願番号基準で和暦変換を行う。
         INPUT: jp:doc-number e.g. 2000123456
         OUTPUT: 昭和|平成NN年
         ====================================================================-->
    <xsl:template name="和暦変換">
        <xsl:variable name="day" select="normalize-space(.)" />
        <xsl:variable name="year" as="xs:integer" select="xs:integer(substring($day, 1, 4))" />
        <xsl:variable name="doc-number" as="xs:integer" select="xs:integer(substring($day, 1, 10))" />
        <xsl:choose>
            <!--　四法が対象外　-->
            <xsl:when
                test="(ancestor::jp:application-reference [@jp:kind-of-law != 'patent']
                        and ancestor::jp:application-reference [@jp:kind-of-law != 'utility']
                        and ancestor::jp:application-reference [@jp:kind-of-law != 'design']
                        and ancestor::jp:application-reference [@jp:kind-of-law != 'trademark']) or
                    not(ancestor::jp:application-reference [@jp:kind-of-law]) ">
                <xsl:choose>
                    <xsl:when test="$year &gt;= 1989">
                        <xsl:call-template name="平成編集" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="昭和編集" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <!--　出願番号　-->
            <xsl:when
                test="ancestor::jp:application-reference
                    and ancestor::jp:application-reference [@appl-type = 'application']">
                <xsl:choose>
                    <xsl:when test="ancestor::jp:application-reference [@jp:kind-of-law = 'patent']">
                        <xsl:choose>
                            <xsl:when test="$doc-number &gt; 1989001146">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when
                        test="ancestor::jp:application-reference [@jp:kind-of-law = 'utility']">
                        <xsl:choose>
                            <xsl:when test="$doc-number &gt; 1989000491">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when test="ancestor::jp:application-reference [@jp:kind-of-law = 'design']">
                        <xsl:choose>
                            <xsl:when test="$doc-number &gt; 1989000124">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when
                        test="ancestor::jp:application-reference [@jp:kind-of-law = 'trademark']">
                        <xsl:choose>
                            <xsl:when test="$doc-number &gt; 1989000354">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <!--　公告番号　-->
            <xsl:when
                test="ancestor::jp:application-reference
                    and ancestor::jp:application-reference [@appl-type = 'examined-pub']">
                <xsl:choose>
                    <xsl:when test="ancestor::jp:application-reference [@jp:kind-of-law = 'patent']">
                        <xsl:choose>
                            <xsl:when test="$doc-number &gt; 1989000600">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when
                        test="ancestor::jp:application-reference [@jp:kind-of-law = 'utility']">
                        <xsl:choose>
                            <xsl:when test="$doc-number &gt; 1989000480">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when
                        test="ancestor::jp:application-reference [@jp:kind-of-law = 'trademark']">
                        <xsl:choose>
                            <xsl:when test="$doc-number &gt; 1989000000">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <!--　公開番号　-->
            <xsl:when
                test="ancestor::jp:application-reference
                    and ancestor::jp:application-reference [@appl-type = 'un-examined-pub']">
                <xsl:choose>
                    <xsl:when test="ancestor::jp:application-reference [@jp:kind-of-law = 'patent']">
                        <xsl:choose>
                            <xsl:when test="$doc-number &gt; 1989003200">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when
                        test="ancestor::jp:application-reference [@jp:kind-of-law = 'utility']">
                        <xsl:choose>
                            <xsl:when test="$doc-number &gt; 1989001800">
                                <xsl:call-template name="平成編集" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="昭和編集" />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                </xsl:choose>
            </xsl:when>
            <!--　審判番号　-->
            <xsl:when test="ancestor::jp:appeal-reference">
                <xsl:choose>
                    <xsl:when test="$doc-number&gt; 198900000">
                        <xsl:call-template name="平成編集" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="昭和編集" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ====================================================================
         平成編集
         INPUT: xs:string contains [0-9]+ in jp:doc-number
         OUTPUT: 平成NN年 
         ====================================================================-->
    <xsl:template name="平成編集">
        <xsl:variable name="year" as="xs:integer"
            select="xs:integer(substring(normalize-space(.),1,4))" />
        <xsl:variable name="hyy" select="$year - 1988" />
        <xsl:value-of select="'平成' || $hyy || '年'" />
    </xsl:template>

    <!-- ====================================================================
         昭和編集
         INPUT: xs:string contains [0-9]+ in jp:doc-number
         OUTPUT: 昭和NN年 
         ====================================================================-->
    <xsl:template name="昭和編集">
        <xsl:variable name="year" as="xs:integer"
            select="xs:integer(substring(normalize-space(.),1,4))" />
        <xsl:variable name="syy" select="$year - 1925" />
        <xsl:value-of select="'昭和' || $syy || '年'" />
    </xsl:template>


</xsl:stylesheet>