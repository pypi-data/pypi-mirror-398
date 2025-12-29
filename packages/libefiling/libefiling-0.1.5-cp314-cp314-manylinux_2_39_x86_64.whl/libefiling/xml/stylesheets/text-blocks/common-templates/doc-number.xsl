<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp">

    <!-- this xslt was created with reference to pat_common.xsl
         of Internet Application Software version i5.30 provided by JPO -->

    <!-- 出願番号等の変換関連のテンプレート-->

    <!-- 出願番号の変換
      INPUT:
        $number : 出願番号文字列 (10桁)
        $law : 法律の種類 (patent, utility, design, trademark)
        $kinddoc : 文書種類要素名 (jp:payment-r100 など)
      -->
    <xsl:template name="translate-application-number">
        <xsl:param name="number" as="xs:string" />
        <xsl:param name="law" as="xs:string" />
        <xsl:param name="kinddoc" as="xs:string" />

        <xsl:choose>
            <xsl:when test="string-length($number) != 10">
                <xsl:value-of select="書誌編集エラー処理" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="number($number) &gt;= 2000000000">
                        <xsl:choose>
                            <xsl:when test="$law = 'patent'">
                                <xsl:value-of select="'特願'" />
                            </xsl:when>
                            <xsl:when test="$law = 'utility'">
                                <xsl:value-of select="'実願'" />
                            </xsl:when>
                            <xsl:when test="$law = 'design'">
                                <xsl:value-of select="'意願'" />
                            </xsl:when>
                            <xsl:when test="$law = 'trademark'">
                                <xsl:value-of select="'商願'" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="'　　'" />
                            </xsl:otherwise>
                        </xsl:choose>
                        <!-- '.' に含まれる後半6桁については, オリジナル pat_common.xslでは先頭から続く0はスペースに変換していた。
                             '2001000001' -> '2001-     1'
                             ここでは  0 そのまま表示する。
                             '2001000001' -> '2001-000001'
                        -->
                        <xsl:value-of
                            select="substring($number,1,4) || '-' || substring($number, 5)" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="和暦変換" />
                        <xsl:choose>
                            <xsl:when test="$law = 'patent'">
                                <xsl:value-of select="'特許願'" />
                            </xsl:when>
                            <xsl:when test="$law = 'utility'">
                                <xsl:value-of select="'実用新案登録願'" />
                            </xsl:when>
                            <xsl:when test="$law = 'design'">
                                <xsl:value-of select="'意匠登録願'" />
                            </xsl:when>
                            <xsl:when test="$law = 'trademark'">
                                <xsl:choose>
                                    <xsl:when
                                        test="$kinddoc = 'jp:payment-r100' or $kinddoc = 'jp:payment-r110'">
                                        <xsl:value-of select="'商標登録願'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="$kinddoc = 'jp:payment-r103' or $kinddoc = 'jp:payment-r113'">
                                        <xsl:value-of select="'防護標章登録願'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="$kinddoc = 'jp:payment-r104' or $kinddoc = 'jp:payment-r114'">
                                        <xsl:value-of select="'商標更新登録願'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="$kinddoc = 'jp:payment-r105' or $kinddoc = 'jp:payment-r115'">
                                        <xsl:value-of select="'防護標章更新登録願'" />
                                    </xsl:when>
                                </xsl:choose>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="'　　'" />
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:value-of select="'第' || substring($number, 5) || '号'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- 国際出願番号の変換
      INPUT:
        $number : 出願番号文字列 (10桁)
      -->
    <xsl:template name="translate-intl-application-number">
        <xsl:param name="number" as="xs:string" />

        <xsl:choose>
            <xsl:when test="string-length($number) = 12">
                <xsl:value-of
                    select="'PCT/' || substring($number,1,6) || '/' || substring($number,7,6)" />
            </xsl:when>
            <xsl:when test="string-length($number) = 9">
                <xsl:value-of
                    select="'PCT/' || substring($number,1,4) || '/' || substring($number,5,5)" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="書誌編集エラー処理" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- 登録番号の変換
      INPUT:
        $number : 登録番号文字列
        $law : 法律の種類 (patent, utility, design, trademark)
      -->
    <xsl:template name="translate-registered-number">
        <xsl:param name="number" as="xs:string" />
        <xsl:param name="law" as="xs:string" />

        <xsl:choose>
            <xsl:when
                test="($law = 'patent' and string-length($number) != 7)
                    or ($law = 'utility' and string-length($number) != 7)">
                <xsl:value-of select="書誌編集エラー処理" />
            </xsl:when>
            <xsl:when
                test="($law != 'patent' and $law != 'utility')
                    and (string-length($number) &lt; 7)">
                <xsl:value-of select="書誌編集エラー処理" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="$law = 'patent'">
                        <xsl:value-of select="'特許第'" />
                    </xsl:when>
                    <xsl:when test="$law = 'utility'">
                        <xsl:value-of select="'実用新案登録第'" />
                    </xsl:when>
                    <xsl:when test="$law = 'design'">
                        <xsl:value-of select="'意匠登録第'" />
                    </xsl:when>
                    <xsl:when test="$law = 'trademark'">
                        <xsl:value-of select="'商標登録第'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="'　　第'" />
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:value-of select="substring($number, 1, 7) || '号'" />
                <xsl:if test="string-length($number) &gt;= 8">
                    <xsl:value-of select="substring($number,8)" />
                </xsl:if>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- 公告番号の変換
        INPUT:
            $number : 公告番号文字列 (10桁)
            $law : 法律の種類 (patent, utility, trademark)
      -->
    <xsl:template name="translate-examind-pub-number">
        <xsl:param name="number" as="xs:string" />
        <xsl:param name="law" as="xs:string" />

        <xsl:choose>
            <xsl:when test="string-length($number) != 10">
                <xsl:value-of select="書誌編集エラー処理" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="和暦変換" />
                <xsl:choose>
                    <xsl:when test="$law = 'patent'">
                        <xsl:value-of select="'特許'" />
                    </xsl:when>
                    <xsl:when test="$law = 'utility'">
                        <xsl:value-of select="'実用新案'" />
                    </xsl:when>
                    <xsl:when test="$law = 'trademark'">
                        <xsl:value-of select="'商標'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:value-of select="'出願公告第' || substring($number, 5, 6) || '号'" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- 公開番号の変換
        INPUT:
            $number : 公開番号文字列 (10桁)
            $law : 法律の種類 (patent, utility)
      -->
    <xsl:template name="translate-pub-number">
        <xsl:param name="number" as="xs:string" />
        <xsl:param name="law" as="xs:string" />

        <xsl:choose>
            <xsl:when test="string-length($number) != 10">
                <xsl:value-of select="書誌編集エラー処理" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="xs:integer($number) &gt;= 2000000000">
                        <xsl:choose>
                            <xsl:when test="$law = 'patent'">
                                <xsl:value-of select="'特開'" />
                            </xsl:when>
                            <xsl:when test="$law = 'utility'">
                                <xsl:value-of select="'実開'" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="書誌編集エラー処理" />
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:value-of
                            select="substring($number,1,4) || '-' || substring($number, 5, 6)" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="和暦変換" />
                        <xsl:choose>
                            <xsl:when test="$law = 'patent'">
                                <xsl:value-of select="'特許'" />
                            </xsl:when>
                            <xsl:when test="$law = 'utility'">
                                <xsl:value-of select="'実用新案'" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="書誌編集エラー処理" />
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:value-of select="'出願公開第' || substring($number, 5, 6) || '号'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- 審判番号の変換
        INPUT:
            $number : 審判番号文字列 (9桁または10桁)
      -->
    <xsl:template name="translate-appeal-number">
        <xsl:param name="number" as="xs:string" />
        <xsl:variable name="lower-5digits" as="xs:integer"
            select="xs:integer(substring($number, 5, 5))" />
        <xsl:variable name="lower-6digits" as="xs:integer"
            select="xs:integer(substring($number, 5, 6))" />

        <xsl:choose>
            <xsl:when test="string-length($number) = 9">
                <xsl:choose>
                    <xsl:when test="number($number) &gt;= 200700000">
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:choose>
                            <xsl:when test="number($number) &gt;= 200000000">
                                <xsl:choose>
                                    <xsl:when
                                        test="1 &lt;= $lower-5digits and $lower-5digits &lt;= 30000">
                                        <xsl:value-of select="'不服'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="30001 &lt;= $lower-5digits and $lower-5digits  &lt;= 35000">
                                        <xsl:value-of select="'取消'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="35001 &lt;= $lower-5digits and $lower-5digits  &lt;= 39000">
                                        <xsl:value-of select="'無効'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="39001 &lt;= $lower-5digits and $lower-5digits  &lt;= 40000">
                                        <xsl:value-of select="'訂正'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="40001 &lt;= $lower-5digits and $lower-5digits  &lt;= 50000">
                                        <xsl:value-of select="'無効'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="50001 &lt;= $lower-5digits and $lower-5digits  &lt;= 60000">
                                        <xsl:value-of select="'補正'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="60001 &lt;= $lower-5digits and $lower-5digits  &lt;= 65000">
                                        <xsl:value-of select="'判定'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="65001 &lt;= $lower-5digits and $lower-5digits  &lt;= 66000">
                                        <xsl:value-of select="'不服'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="66001 &lt;= $lower-5digits and $lower-5digits  &lt;= 67000">
                                        <xsl:value-of select="'取消'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="67001 &lt;= $lower-5digits and $lower-5digits  &lt;= 68000">
                                        <xsl:value-of select="'無効'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="68001 &lt;= $lower-5digits and $lower-5digits  &lt;= 69000">
                                        <xsl:value-of select="'異議'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="69001 &lt;= $lower-5digits and $lower-5digits  &lt;= 69500">
                                        <xsl:value-of select="'補正'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="69501 &lt;= $lower-5digits and $lower-5digits  &lt;= 69600">
                                        <xsl:value-of select="'判定'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="69601 &lt;= $lower-5digits and $lower-5digits  &lt;= 69700">
                                        <xsl:value-of select="'再審'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="69701 &lt;= $lower-5digits and $lower-5digits  &lt;= 69800">
                                        <xsl:value-of select="'除斥'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="69801 &lt;= $lower-5digits and $lower-5digits  &lt;= 69900">
                                        <xsl:value-of select="'忌避'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="69901 &lt;= $lower-5digits and $lower-5digits  &lt;= 70000">
                                        <xsl:value-of select="'証拠'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="70001 &lt;= $lower-5digits and $lower-5digits  &lt;= 95000">
                                        <xsl:choose>
                                            <xsl:when
                                                test="number($number) &gt;= 200400000 and 80001 &lt;= $lower-5digits and $lower-5digits  &lt;= 90000">
                                                <xsl:value-of select="'無効'" />
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <xsl:value-of select="'異議'" />
                                            </xsl:otherwise>
                                        </xsl:choose>
                                    </xsl:when>
                                    <xsl:when
                                        test="95001 &lt;= $lower-5digits and $lower-5digits  &lt;= 96000">
                                        <xsl:value-of select="'再審'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="96001 &lt;= $lower-5digits and $lower-5digits  &lt;= 97000">
                                        <xsl:value-of select="'除斥'" />
                                    </xsl:when>
                                    <xsl:when
                                        test="97001 &lt;= $lower-5digits and $lower-5digits  &lt;= 98000">
                                        <xsl:value-of select="'忌避'" />
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:value-of select="'証拠'" />
                                    </xsl:otherwise>
                                </xsl:choose>
                                <xsl:value-of select="substring($number,1,4) || '-'" />
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="和暦変換" />
                                <xsl:value-of select="'審判第'" />
                            </xsl:otherwise>
                        </xsl:choose>
                        <xsl:value-of select="substring($number, 5, 5)" />
                        <xsl:if test="number($number) &lt; 200000000">
                            <xsl:value-of select="'号'" />
                        </xsl:if>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="string-length($number) = 10">
                <xsl:choose>
                    <xsl:when test="number($number) &gt;= 2007000001">
                        <xsl:choose>
                            <xsl:when test="1 &lt;= $lower-6digits and $lower-6digits &lt;= 199999">
                                <xsl:value-of select="'不服'" />
                            </xsl:when>
                            <xsl:when
                                test="300001 &lt;= $lower-6digits and $lower-6digits  &lt;= 349999">
                                <xsl:value-of select="'取消'" />
                            </xsl:when>
                            <xsl:when
                                test="390001 &lt;= $lower-6digits and $lower-6digits  &lt;= 399999">
                                <xsl:value-of select="'訂正'" />
                            </xsl:when>
                            <xsl:when
                                test="400001 &lt;= $lower-6digits and $lower-6digits  &lt;= 409999">
                                <xsl:value-of select="'無効'" />
                            </xsl:when>
                            <xsl:when
                                test="500001 &lt;= $lower-6digits and $lower-6digits  &lt;= 509999">
                                <xsl:value-of select="'補正'" />
                            </xsl:when>
                            <xsl:when
                                test="600001 &lt;= $lower-6digits and $lower-6digits  &lt;= 609999">
                                <xsl:value-of select="'判定'" />
                            </xsl:when>
                            <xsl:when
                                test="650001 &lt;= $lower-6digits and $lower-6digits  &lt;= 669999">
                                <xsl:value-of select="'不服'" />
                            </xsl:when>
                            <xsl:when
                                test="670001 &lt;= $lower-6digits and $lower-6digits  &lt;= 679999">
                                <xsl:value-of select="'取消'" />
                            </xsl:when>
                            <xsl:when
                                test="680001 &lt;= $lower-6digits and $lower-6digits  &lt;= 684999">
                                <xsl:value-of select="'無効'" />
                            </xsl:when>
                            <xsl:when
                                test="685001 &lt;= $lower-6digits and $lower-6digits  &lt;= 689999">
                                <xsl:value-of select="'異議'" />
                            </xsl:when>
                            <xsl:when
                                test="690001 &lt;= $lower-6digits and $lower-6digits  &lt;= 694999">
                                <xsl:value-of select="'補正'" />
                            </xsl:when>
                            <xsl:when
                                test="695001 &lt;= $lower-6digits and $lower-6digits  &lt;= 695999">
                                <xsl:value-of select="'判定'" />
                            </xsl:when>
                            <xsl:when
                                test="696001 &lt;= $lower-6digits and $lower-6digits  &lt;= 696999">
                                <xsl:value-of select="'再審'" />
                            </xsl:when>
                            <xsl:when
                                test="697001 &lt;= $lower-6digits and $lower-6digits  &lt;= 697999">
                                <xsl:value-of select="'除斥'" />
                            </xsl:when>
                            <xsl:when
                                test="698001 &lt;= $lower-6digits and $lower-6digits  &lt;= 698999">
                                <xsl:value-of select="'忌避'" />
                            </xsl:when>
                            <xsl:when
                                test="699001 &lt;= $lower-6digits and $lower-6digits  &lt;= 699999">
                                <xsl:value-of select="'証拠'" />
                            </xsl:when>
                            <xsl:when
                                test="700001 &lt;= $lower-6digits and $lower-6digits  &lt;= 799999">
                                <xsl:value-of select="'異議'" />
                            </xsl:when>
                            <xsl:when
                                test="800001 &lt;= $lower-6digits and $lower-6digits  &lt;= 899999">
                                <xsl:value-of select="'無効'" />
                            </xsl:when>
                            <xsl:when
                                test="900001 &lt;= $lower-6digits and $lower-6digits  &lt;= 909999">
                                <xsl:value-of select="'異議'" />
                            </xsl:when>
                            <xsl:when
                                test="950001 &lt;= $lower-6digits and $lower-6digits  &lt;= 959999">
                                <xsl:value-of select="'再審'" />
                            </xsl:when>
                            <xsl:when
                                test="960001 &lt;= $lower-6digits and $lower-6digits  &lt;= 969999">
                                <xsl:value-of select="'除斥'" />
                            </xsl:when>
                            <xsl:when
                                test="970001 &lt;= $lower-6digits and $lower-6digits  &lt;= 979999">
                                <xsl:value-of select="'忌避'" />
                            </xsl:when>
                            <xsl:when
                                test="980001 &lt;= $lower-6digits and $lower-6digits  &lt;= 989999">
                                <xsl:value-of select="'証拠'" />
                            </xsl:when>
                        </xsl:choose>
                        <xsl:value-of
                            select="substring($number,1,4) || '-' || substring($number, 5, 6)" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="書誌編集エラー処理" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

</xsl:stylesheet>