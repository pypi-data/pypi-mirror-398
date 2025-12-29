<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp">

    <!-- this xslt was created with reference to pat_common.xsl
         of Internet Application Software version i5.30 provided by JPO -->

    <!-- 元は pat_common.xslだが pat-app-doc.xsl に特化させた.
         補正や発送、請求などを考慮した出力を削除した。-->

    <!-- TODO: tag1//tag2 としたtemplateはdtd確認
     call-template='error -> value-of erro の確認
     -->

    <xsl:variable name="doc-code" select="normalize-space(/descendant::jp:document-code[1])" /> <!--
    先頭の書類識別コードを取得 -->
    <xsl:variable name="payment" select="substring($node,1,11)" />

    <!-- ====================================================================
         jp:document-code
         ====================================================================-->
    <!-- 書類識別コード -->
    <xsl:template match="jp:document-code">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【書類名】'" />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="convert-document-code">
                    <xsl:with-param name="code" select="." />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:special-mention-matter-article
         ====================================================================-->
    <!-- 特記事項 -->
    <xsl:template match="jp:special-mention-matter-article">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="normalize-space()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【特記事項】'" />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="convert-special-mention-matter-article">
                    <xsl:with-param name="article" select="normalize-space()" />
                    <xsl:with-param name="kind-of-law" select="$kind-of-law" />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:submission-date 提出日 
         jp:dispatch-date 発送日 
         jp:priority-claim 出願日
         jp:appeal-reference 審判請求日
         ====================================================================-->
    <xsl:template
        match="jp:submission-date/jp:date | jp:dispatch-date/jp:date |
               jp:priority-claim/jp:date | jp:appeal-reference/jp:date">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="normalize-space()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:choose>
                    <xsl:when test="parent::jp:submission-date">
                        <xsl:text>【提出日】</xsl:text>
                    </xsl:when>
                    <xsl:when test="parent::jp:dispatch-date">
                        <xsl:text>【発送日】</xsl:text>
                    </xsl:when>
                    <xsl:when test="parent::jp:priority-claim">
                        <xsl:text>【出願日】</xsl:text>
                    </xsl:when>
                    <xsl:when test="parent::jp:appeal-reference">
                        <xsl:text>【審判請求日】</xsl:text>
                    </xsl:when>
                </xsl:choose>
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="format-date-jp">
                    <xsl:with-param name="date-str" select="normalize-space()" />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <xsl:template match="jp:application-reference//jp:date">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="normalize-space()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:choose>
                    <xsl:when
                        test="ancestor::jp:application-reference
                    and ancestor::jp:application-reference [@appl-type = 'application']">
                        <xsl:value-of select="'【出願日】'" />
                    </xsl:when>
                    <xsl:when
                        test="ancestor::jp:application-reference
                    and ancestor::jp:application-reference [@appl-type = 'international-application']">
                        <xsl:value-of select="'【国際出願日】'" />
                    </xsl:when>
                    <xsl:when
                        test="ancestor::jp:application-reference
                    and ancestor::jp:application-reference [@appl-type = 'registration']">
                        <xsl:value-of select="'【登録日】'" />
                    </xsl:when>
                </xsl:choose>
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="format-date-jp">
                    <xsl:with-param name="date-str" select="normalize-space()" />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         原出願の表示編集
         <xsl:template name="原出願の表示編集">
         ====================================================================-->
    <xsl:template match="jp:parent-application-article">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:choose>
                    <xsl:when test="./@jp:kind-of-application = 'based-on-utility'">
                        <xsl:value-of select="'【基礎とした実用新案登録及びその実用新案登録出願の表示】'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="'【原出願の表示】'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
            <xsl:apply-templates
                select="jp:application-reference [@appl-type = 'registration']//jp:doc-number" />
            <xsl:apply-templates select="jp:application-reference [@appl-type = 'registration']" />
            <xsl:apply-templates
                select="jp:application-reference [@appl-type = 'application']//jp:doc-number" />
            <xsl:apply-templates
                select="jp:application-reference [@appl-type = 'application']//jp:date" />
            <xsl:apply-templates
                select="jp:application-reference [@appl-type = 'international-application']//jp:doc-number" />
            <xsl:apply-templates
                select="jp:application-reference [@appl-type = 'international-application']" />
            <xsl:apply-templates select="jp:file-reference-id" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:application-reference 基礎出願の文書番号変換
         ====================================================================-->
    <xsl:template match="jp:application-reference[@appl-type = 'application']//jp:doc-number">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="normalize-space()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【出願番号】'" />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="translate-application-number">
                    <xsl:with-param name="number" select="normalize-space()" />
                    <xsl:with-param name="law" select="$kind-of-law" />
                    <xsl:with-param name="kinddoc" select="$node" />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:application-reference 基礎登録の文書番号変換
         ====================================================================-->
    <xsl:template match="jp:application-reference[@appl-type = 'registration']//jp:doc-number">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="normalize-space()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:choose>
                    <xsl:when test="$kind-of-law = 'patent'">
                        <xsl:value-of select="'【特許番号】'" />
                    </xsl:when>
                    <xsl:when test="$kind-of-law = 'utility'">
                        <xsl:value-of select="'【実用新案登録番号】'" />
                    </xsl:when>
                    <xsl:when test="$kind-of-law = 'design'">
                        <xsl:value-of select="'【意匠登録番号】'" />
                    </xsl:when>
                    <xsl:when test="$kind-of-law = 'trademark'">
                        <xsl:value-of select="'【商標登録番号】'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="'【登録番号】'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="translate-registered-number">
                    <xsl:with-param name="number" select="normalize-space()" />
                    <xsl:with-param name="law" select="$kind-of-law" />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:application-reference 基礎国際出願の文書番号変換
         ====================================================================-->
    <xsl:template
        match="jp:application-reference [@appl-type = 'international-application']//jp:doc-number">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="normalize-space()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【国際出願番号】'" />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="translate-intl-application-number">
                    <xsl:with-param name="number" select="normalize-space()" />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:priority-claim パリ条約基礎出願の文書番号変換
         ====================================================================-->
    <xsl:template match="jp:priority-claim/jp:doc-number">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="normalize-space()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【出願番号】'" />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:application-reference 出願公告の文書番号変換
         ====================================================================-->
    <xsl:template match="jp:application-reference[@appl-type = 'examined-pub']//jp:doc-number">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="normalize-space()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【出願公告番号】'" />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="translate-examind-pub-number">
                    <xsl:with-param name="number" select="normalize-space()" />
                    <xsl:with-param name="law" select="$kind-of-law" />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:application-reference 出願公開の文書番号変換
         ====================================================================-->
    <xsl:template match="jp:application-reference[@appl-type = 'un-examined-pub']//jp:doc-number">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="normalize-space()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【出願公開番号】'" />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="translate-pub-number">
                    <xsl:with-param name="number" select="normalize-space()" />
                    <xsl:with-param name="law" select="$kind-of-law" />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:appeal-reference 審判の文書番号変換
         ====================================================================-->
    <xsl:template match="jp:appeal-reference/jp:doc-number">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="normalize-space()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【審判番号】'" />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="translate-appeal-number">
                    <xsl:with-param name="number" select="normalize-space()" />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:application-reference 出願書類参照
         ====================================================================-->
    <xsl:template match="jp:application-reference">
        <xsl:choose>
            <xsl:when test="parent::jp:earlier-app or parent::jp:parent-application-article">
                <xsl:call-template name="出願書類参照編集" />
                <xsl:if test=".//jp:date">
                    <xsl:choose>
                        <xsl:when test="./@appl-type = 'application'">
                            <xsl:choose>
                                <xsl:when
                                    test="
                                        ((./@appl-type='application') and (.//jp:doc-number !='')) or
                                        ((following-sibling::jp:application-reference/@appl-type='application' or
                                                following-sibling::jp:application-reference/@appl-type='international-application') and
                                            (following-sibling::jp:application-reference//jp:doc-number !=''))  or
                                        ((preceding-sibling::jp:application-reference/@appl-type='application' or
                                                preceding-sibling::jp:application-reference/@appl-type='international-application') and
                                            (preceding-sibling::jp:application-reference//jp:doc-number !=''))">
                                    <xsl:call-template name="先の出願日編集" />
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:apply-templates select=".//jp:date" />
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:apply-templates select=".//jp:date" />
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:if>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="jp:document-id/jp:doc-number" />
                <xsl:call-template name="出願書類参照編集" />
                <xsl:apply-templates select="jp:document-id/jp:date" />
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- ====================================================================
         出願書類参照編集
         ====================================================================-->
    <xsl:template name="出願書類参照編集">
        <xsl:if
            test="(ancestor::jp:indication-of-case-article
                        or ancestor::jp:parent-application-article)
                    and (./@appl-type = 'international-application')
                    and (./@jp:kind-of-law)">

            <xsl:element name="blocks">
                <xsl:element name="tag">
                    <xsl:value-of select="local-name()" />
                </xsl:element>
                <xsl:element name="text">
                    <xsl:value-of select="normalize-space()" />
                </xsl:element>
                <xsl:element name="jp-tag">
                    <xsl:value-of select="'【出願の区分】'" />
                </xsl:element>
                <xsl:element name="converted-text">
                    <xsl:choose>
                        <xsl:when test="./@jp:kind-of-law = 'patent'">
                            <xsl:value-of select="'特許'" />
                        </xsl:when>
                        <xsl:when test="./@jp:kind-of-law = 'utility'">
                            <xsl:value-of select="'実用新案登録'" />
                        </xsl:when>
                        <xsl:when test="./@jp:kind-of-law = ''">
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="書誌編集エラー処理" />
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:element>
            </xsl:element>
        </xsl:if>
    </xsl:template>

    <!-- ====================================================================
         先の出願日編集
         ====================================================================-->
    <xsl:template name="先の出願日編集">
        <xsl:variable name="date-str" select="normalize-space(.//jp:date)" />
        <xsl:variable name="m" select="substring(normalize-space(.//jp:date),5,2)" />
        <xsl:variable name="d" select="substring(normalize-space(.//jp:date),7,2)" />

        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="$date-str" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【出願日】'" />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:choose>
                    <xsl:when test=".//jp:date/@jp:error-code">
                        <xsl:value-of select=".//jp:date" />
                    </xsl:when>
                    <xsl:when test="string-length($date-str) != 8" />
                    <xsl:when
                        test="(number(.//jp:date) != number($date-str)) or (number($date-str) &lt; 19260101)">
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:when>
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
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:ipc-article 国際特許分類編集 
         <xsl:template name="国際特許分類編集">
         ====================================================================-->
    <xsl:template match="jp:ipc-article">
        <xsl:for-each select="jp:ipc">
            <xsl:element name="blocks">
                <xsl:element name="tag">
                    <xsl:text>ipc</xsl:text>
                </xsl:element>
                <xsl:choose>
                    <xsl:when test="position() = 1">
                        <xsl:element name="jp-tag">
                            <xsl:value-of select="'【国際特許分類】'" />
                        </xsl:element>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:element name="jp-tag">
                            <xsl:value-of select="''" />
                        </xsl:element>
                    </xsl:otherwise>
                </xsl:choose>
                <xsl:element name="text">
                    <xsl:value-of select="normalize-space()" />
                </xsl:element>
            </xsl:element>
        </xsl:for-each>
    </xsl:template>

    <!-- ====================================================================
         jp:inventors 発明者の記事
         ====================================================================-->
    <xsl:template match="jp:inventors">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:apply-templates select="jp:inventor" />
        </xsl:element>
    </xsl:template>


    <!-- ====================================================================
         発明者編集
         <xsl:template name="発明者編集">
         ====================================================================-->
    <xsl:template match="jp:inventor">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:choose>
                    <xsl:when test="$kind-of-law = 'patent'">
                        <xsl:value-of select="'【発明者】'" />
                    </xsl:when>
                    <xsl:when test="$kind-of-law = 'utility'">
                        <xsl:value-of select="'【考案者】'" />
                    </xsl:when>
                </xsl:choose>
            </xsl:element>

            <xsl:apply-templates select=".//jp:registered-number" />
            <xsl:apply-templates select=".//jp:text" />
            <xsl:apply-templates select=".//jp:kana" />
            <xsl:apply-templates select=".//jp:name" />
        </xsl:element>
    </xsl:template>

    <xsl:template match="jp:inventor//jp:name">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【氏名】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:applicants 申請者の記事
         jp:applicant-of-case-article 事件の出願人の記事
         jp:presenter-article 提出者の記事
         ==================================================================== -->
    <xsl:template match="jp:applicants">
        <!-- | jp:applicant-of-case-article | jp:presenter-article"> -->
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:apply-templates select="jp:applicant" />
        </xsl:element>
    </xsl:template>

    <xsl:template match="jp:applicants/jp:applicant">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <!-- オリジナルの<xsl:template name="申請者前編集">
                 から必要部分を抜き取った -->
                <xsl:choose>
                    <xsl:when test="./@jp:kind-of-application = 'appeal'">
                        <xsl:value-of select="'【審判請求人】'" />
                    </xsl:when>
                    <xsl:when
                        test="matches($doc-code, '^A263[2-6]?$')">
                        <xsl:value-of select="'【実用新案登録出願人】'" />
                    </xsl:when>
                    <xsl:when
                        test="matches($doc-code, '^A163[1245]?$')">
                        <xsl:value-of select="'【特許出願人】'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
            <xsl:call-template name="applicant" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         original: template match=jp:applicant
         ====================================================================-->
    <xsl:template name="applicant">
        <xsl:apply-templates select="jp:relation-of-case" />
        <xsl:if test="ancestor::jp:applicants or ancestor::jp:presenter-article">
            <xsl:apply-templates select="jp:share" />
            <xsl:apply-templates select="jp:representative-applicant" />
        </xsl:if>
        <xsl:apply-templates select=".//jp:registered-number" />
        <xsl:apply-templates select=".//jp:text" />
        <xsl:if test="ancestor::jp:applicants or ancestor::jp:presenter-article">
            <xsl:apply-templates select=".//jp:original-language-of-address" />
        </xsl:if>
        <xsl:apply-templates select="jp:addressbook/jp:kana" />
        <xsl:apply-templates select="jp:addressbook/jp:name" />
        <xsl:if test="ancestor::jp:applicants or ancestor::jp:presenter-article">
            <xsl:apply-templates select="jp:addressbook/jp:original-language-of-name" />
        </xsl:if>
        <xsl:if test="ancestor::jp:applicants or ancestor::jp:presenter-article">
            <xsl:apply-templates select="jp:office-address" />
            <xsl:apply-templates select="jp:office-in-japan" />
            <xsl:apply-templates select="jp:office" />
        </xsl:if>
        <xsl:apply-templates select="jp:representative-group" />
        <xsl:if test="ancestor::jp:applicants or ancestor::jp:presenter-article">
            <xsl:apply-templates select="jp:legal-entity-property" />
        </xsl:if>
        <xsl:apply-templates select="jp:nationality" />
        <xsl:apply-templates select=".//jp:phone" />
        <xsl:apply-templates select=".//jp:fax" />
        <xsl:apply-templates select="jp:contact" />
    </xsl:template>


    <!-- ====================================================================
         jp:share-rate 持分の割合編集
         <xsl:template name="持分の割合編集">
         ====================================================================-->
    <xsl:template match="jp:share-rate">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【持分の割合】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="jp:moleclar" />
                <xsl:text> / </xsl:text>
                <xsl:value-of select="jp:denominator" />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         氏名又は名称原語表記編集 の書換
         original <xsl:template name="氏名又は名称原語表記編集">
         jp:applicant or jp:agent 
           /jp:representative-group?/jp:representative+/
           (jp:kana?,jp:representative-identification?,jp:name?,
            jp:original-language-of-name?)
         ====================================================================-->
    <xsl:template match="jp:representative/jp:original-language-of-name">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:text>【</xsl:text> select="' ' || $meisyo || ' '" /> <xsl:value-of
                    select="normalize-space(preceding-sibling::jp:representative-identification)" />
                <xsl:text>原語表記】</xsl:text>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:agents 代理人の記事
         ==================================================================== -->
    <xsl:template match="jp:agents | jp:attorney-change-article">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:apply-templates select="jp:agent" />
        </xsl:element>
    </xsl:template>

    <xsl:template match="jp:agents/jp:agent | jp:attorney-change-article/jp:agent">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:choose>
                    <xsl:when test="./@jp:kind-of-agent">
                        <xsl:call-template name="code-to-agents1">
                            <xsl:with-param name="code" select="$doc-code" />
                        </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:call-template name="code-to-agents2">
                            <xsl:with-param name="code" select="$doc-code" />
                        </xsl:call-template>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
            <xsl:call-template name="agent" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
        pat-app-doc 用 代理人コード変換テンプレート
        INPUT: $code 書類コード
        OUTPUT: 代理人の種類を表す文字列

        <jp:agent jp:kind-of-agent> コンテキストで呼び出されることを想定している。
        pat-app-doc は、↓ を対象としている。
        本テンプレートは、pat-app-doc から読み込まれることを想定している。
        そこで、オリジナルの代理人コード変換テンプレートのうち以下のコードのみに対応した。

          A[1-4]63: 特許願, 実用新案登録願, 意匠登録願，商標登録願
          A1631: 翻訳文提出書
          A[12]632: 国内書面
          A4632: 防護標章登録願
          A2633: 図面の提出書
          A4633: 防護標章登録に基づく権利存続期間更新登録願
          A[12]634: 国際出願翻訳文提出書
          A4634: 書換登録申請書
          A[12]635: 国際出願翻訳文提出書(職権)
          A4635: 防護標章登録に基づく権利書換登録登録申請書
     -->
    <xsl:template name="code-to-agents1">
        <xsl:param name="code" />
        <xsl:choose>
            <xsl:when test="ancestor::jp:agents">
                <xsl:choose>
                    <xsl:when
                        test="
                        matches($code, '^A[12]63$') or
                        matches($code, '^A[12]63[245]$') or
                        $code = 'A1631' or $code = 'A2633'">
                        <xsl:value-of select="'【'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="ancestor::jp:attorney-change-article">
                <xsl:choose>
                    <xsl:when
                        test="matches($code, '^A[12]632?$')">
                        <xsl:value-of select="'【選任した'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="./@jp:kind-of-agent = 'representative'">
                <xsl:value-of select="'代理人'" />
            </xsl:when>
            <xsl:when test="./@jp:kind-of-agent = 'sub-representative'">
                <xsl:value-of select="'復代理人'" />
            </xsl:when>
            <xsl:when test="./@jp:kind-of-agent = 'legal-representative'">
                <xsl:value-of select="'法定代理人'" />
            </xsl:when>
            <xsl:when test="./@jp:kind-of-agent = 'designated-representative'">
                <xsl:value-of select="'指定代理人'" />
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="./@jp:kind-of-agent" />
            </xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="'】'" />
    </xsl:template>

    <!-- ====================================================================
        pat-app-doc 用 代理人コード変換テンプレート
        INPUT: $code 書類コード
        OUTPUT: 代理人の種類を表す文字列

        <jp:agent> コンテキストで呼び出されることを想定している。
        pat-app-doc は、↓ を対象としている。
        本テンプレートは、pat-app-doc から読み込まれることを想定している。
        そこで、オリジナルの代理人コード変換テンプレートのうち以下のコードのみに対応した。

          A[1-4]63: 特許願, 実用新案登録願, 意匠登録願，商標登録願
          A1631: 翻訳文提出書
          A[12]632: 国内書面
          A4632: 防護標章登録願
          A2633: 図面の提出書
          A4633: 防護標章登録に基づく権利存続期間更新登録願
          A[12]634: 国際出願翻訳文提出書
          A4634: 書換登録申請書
          A[12]635: 国際出願翻訳文提出書(職権)
          A4635: 防護標章登録に基づく権利書換登録登録申請書
     -->
    <xsl:template name="code-to-agents2">
        <xsl:param name="code" />
        <xsl:choose>
            <xsl:when test="ancestor::jp:agents">
                <xsl:choose>
                    <xsl:when
                        test="
                        matches($code, '^A[12]63$') or
                        matches($code, '^A[12]63[245]$') or
                        $code = 'A1631' or $code = 'A2633'">
                        <xsl:value-of select="'【代理人】'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <xsl:when test="ancestor::jp:attorney-change-article">
                <xsl:choose>
                    <xsl:when
                        test="matches($code, '^A[12]63$') or
                        matches($code, '^A[12]632$')">
                        <xsl:value-of select="'【選任した代理人】'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <!-- ====================================================================
         代理人前編集
         <xsl:template name="代理人前編集">
         ====================================================================-->
    <xsl:template name="agent">
        <xsl:apply-templates select=".//jp:registered-number" />
        <xsl:apply-templates select=".//jp:text" />
        <xsl:apply-templates select="jp:attorney" />
        <xsl:apply-templates select="jp:lawyer" />
        <xsl:apply-templates select="jp:addressbook/jp:kana" />
        <xsl:apply-templates select="jp:addressbook/jp:name" />
        <xsl:choose>
            <xsl:when test="ancestor::jp:attorney-of-case-article">
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="jp:office-address" />
            </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates select="jp:representative-group" />
        <xsl:apply-templates select=".//jp:phone" />
        <xsl:apply-templates select=".//jp:fax" />
        <xsl:apply-templates select="jp:contact" />
        <xsl:apply-templates select="jp:relation-attorney-special-matter" />
    </xsl:template>

    <!-- ====================================================================
         jp:representative-group 代表者情報
         ====================================================================-->
    <xsl:template match="jp:representative-group">
        <xsl:for-each select="jp:representative">
            <xsl:apply-templates select="jp:kana" />
            <xsl:apply-templates select="jp:name" />
            <xsl:if test="ancestor::jp:applicants or ancestor::jp:presenter-article">
                <xsl:apply-templates select="jp:original-language-of-name" />
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <!-- ====================================================================
         jp:nationality
         ====================================================================-->
    <!-- 国籍 -->
    <xsl:template match="jp:nationality">
        <xsl:apply-templates select="jp:country" />
    </xsl:template>

    <!-- ====================================================================
         jp:country 国コード
         <xsl:template name="国コード編集">
         ====================================================================-->
    <xsl:template match="jp:country">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:choose>
                    <xsl:when test="ancestor::jp:priority-claim">
                        <xsl:value-of select="'【国・地域名】'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="'　　【国籍・地域】　　'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:call-template name="convert-country">
                    <xsl:with-param name="country-code" select="." />
                </xsl:call-template>
            </xsl:element>
        </xsl:element>
    </xsl:template>


    <!-- ====================================================================
         パリ条約による優先権等の主張編集
         <xsl:template name="パリ条約による優先権等の主張編集">
         ====================================================================-->
    <xsl:template match="jp:priority-claims">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:apply-templates select="jp:priority-claim" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:priority-claim パリ優先権主張
         デフォルト(otherwise)だけとりだした
         ====================================================================-->
    <xsl:template match="jp:priority-claim">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【パリ条約による優先権等の主張】'" />
            </xsl:element>
            <xsl:apply-templates select="jp:country" />
            <xsl:apply-templates select="jp:date" />
            <xsl:apply-templates select="jp:doc-number" />
            <xsl:apply-templates select="jp:ip-type" />
            <xsl:apply-templates select="jp:generated-access-code" />
            <xsl:apply-templates select="jp:priority-doc-location-info" />
            <xsl:apply-templates select="jp:use-of-das" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:declaration-priority-ear-app 先の出願に基づく優先権主張
         ====================================================================-->
    <xsl:template match="jp:declaration-priority-ear-app">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:apply-templates select="jp:earlier-app" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:earlier-app 先の出願
         ====================================================================-->
    <xsl:template match="jp:earlier-app">
        <xsl:element name="blocks">

            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【先の出願に基づく優先権主張】'" />
            </xsl:element>

            <xsl:apply-templates
                select="jp:application-reference[@appl-type = 'application']//jp:doc-number" />
            <xsl:apply-templates
                select="jp:application-reference[@appl-type = 'international-application']//jp:doc-number" />
            <xsl:apply-templates select="jp:application-reference" />
            <xsl:apply-templates select="jp:file-reference-id" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:payment-years 納付年分
         <xsl:template name="納付年分編集">
         ====================================================================-->
    <xsl:template match="jp:payment-years">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【納付年分】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:apply-templates select="jp:year-from" />
                <xsl:apply-templates select="jp:year-to" />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:charge-article 手数料の表示編集 のデフォルト(otherwise)を抽出
         <xsl:template name="手数料の表示編集">
         ====================================================================-->
    <xsl:template match="jp:charge-article">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【手数料の表示】'" />
            </xsl:element>
            <xsl:apply-templates select="jp:payment" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:payment 納付
         ====================================================================-->
    <xsl:template match="jp:payment">
        <xsl:apply-templates select="jp:account" />
        <xsl:apply-templates select="jp:fee" />
    </xsl:template>


    <!-- ====================================================================
         jp:account 予納台帳番号・納付書番号
         <xsl:template name="予納台帳番号編集">
         ====================================================================-->
    <xsl:template match="jp:account">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:choose>
                    <xsl:when test="./@account-type = 'deposit'">
                        <xsl:value-of select="'【予納台帳番号】'" />
                    </xsl:when>
                    <xsl:when test="./@account-type = 'form'">
                        <xsl:value-of select="'【納付書番号】'" />
                    </xsl:when>
                    <xsl:when test="./@account-type = 'electronic-cash'">
                        <xsl:value-of select="'【納付番号】'" />
                    </xsl:when>
                    <xsl:when test="./@account-type = 'transfer'">
                        <xsl:value-of select="'【振替番号】'" />
                    </xsl:when>
                    <xsl:when test="./@account-type = 'credit-card'">
                        <xsl:value-of select="'【指定立替納付】'" />
                    </xsl:when>
                </xsl:choose>
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="./@number" />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:choose>
                    <xsl:when test="./@account-type = 'deposit'">
                        <xsl:value-of select="./@number" />
                    </xsl:when>
                    <xsl:when test="./@account-type = 'form'">
                        <xsl:value-of select="./@number" />
                    </xsl:when>
                    <xsl:when test="./@account-type = 'electronic-cash'">
                        <xsl:choose>
                            <xsl:when test="./@jp:error-code">
                                <xsl:value-of select="./@number" />
                            </xsl:when>
                            <xsl:when test="string-length(normalize-space(./@number)) = 0" />
                            <xsl:otherwise>
                                <xsl:call-template name="split-at-n-chars">
                                    <xsl:with-param name="input-string"
                                        select="substring(normalize-space(./@number),1,16)" />
                                    <xsl:with-param name="n-chars" select="4" />
                                    <xsl:with-param name="sep" select="'-'" />
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:when>
                    <xsl:when test="./@account-type = 'transfer'">
                        <xsl:value-of select="./@number" />
                    </xsl:when>
                    <xsl:when test="./@account-type = 'credit-card'">
                        <xsl:if test="./@jp:error-code">
                            <xsl:value-of select="./@number" />
                        </xsl:if>
                    </xsl:when>
                </xsl:choose>
            </xsl:element>
        </xsl:element>
    </xsl:template>


    <!-- ====================================================================
         jp:fee 納付方法・納付金額 のデフォルト(otherwise)を抽出
         ====================================================================-->
    <xsl:template match="jp:fee">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【納付金額】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="./@amount" />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:choose>
                    <xsl:when test="./@jp:error-code">
                        <xsl:value-of select="./@amount" />
                    </xsl:when>
                    <xsl:when
                        test="./@amount != '' and string(number(./@amount)) != 'NaN'">
                        <xsl:value-of
                            select="format-number(xs:integer(normalize-space(./@amount)), '#,###')" />
                        <xsl:value-of select="'円'" />
                    </xsl:when>
                </xsl:choose>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:submission-object-list-article
         ====================================================================-->
    <!-- 提出物件の目録 -->
    <xsl:template match="jp:submission-object-list-article">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【提出物件の目録】'" />
            </xsl:element>
            <xsl:apply-templates select="jp:list-group" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:list-group 目録
         ====================================================================-->
    <xsl:template match="jp:list-group">
        <xsl:apply-templates select="jp:document-name" />
        <xsl:apply-templates select="jp:citation" />
        <xsl:apply-templates select="jp:return-request" />
        <xsl:apply-templates select="jp:general-power-of-attorney-id" />
        <xsl:apply-templates select="jp:dtext" />
    </xsl:template>

    <!-- ====================================================================
         jp:document-name 物件名
         ====================================================================-->
    <xsl:template match="jp:document-name">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【物件名】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:value-of select="." />
                <xsl:text>　</xsl:text>
                <xsl:value-of select="following-sibling::jp:number-of-object" />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:return-reques 返還の申出
         <xsl:template name="返還の申出編集">
         ====================================================================-->
    <xsl:template match="jp:return-request">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【返還の申出】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:choose>
                    <xsl:when test="normalize-space(.) = '0'">
                        <xsl:value-of select="'無'" />
                    </xsl:when>
                    <xsl:when test="normalize-space(.) = '1'">
                        <xsl:value-of select="'有'" />
                    </xsl:when>
                    <xsl:when test="normalize-space(.) = ''">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:proof-necessity プルーフの要否
         <xsl:template name="プルーフの要否編集">
         ====================================================================-->
    <xsl:template match="jp:proof-necessity">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【プルーフの要否】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
            <xsl:element name="converted-text">
                <xsl:choose>
                    <xsl:when test="normalize-space(.) = '0'">
                        <xsl:value-of select="'不要'" />
                    </xsl:when>
                    <xsl:when test="normalize-space(.) = '1'">
                        <xsl:value-of select="'要'" />
                    </xsl:when>
                    <xsl:when test="normalize-space(.) = ''">
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="書誌編集エラー処理" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:rule-outside-item-article
         ====================================================================-->
    <!-- 規定外の項目 -->
    <xsl:template match="jp:rule-outside-item-article">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【規定外の項目】'" />
            </xsl:element>
            <xsl:apply-templates select="jp:rule-outside-group" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:rule-outside-group 規定外記事
         ====================================================================-->
    <xsl:template match="jp:rule-outside-group">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:apply-templates select="jp:item-name" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         項目名編集
         <xsl:template name="項目名編集">
         ====================================================================-->
    <xsl:template match="jp:item-name">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【' || . || '】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:apply-templates select="following-sibling::jp:item-content" />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         事件の表示編集
         <xsl:template name="事件の表示編集">
         ====================================================================-->
    <xsl:template match="jp:indication-of-case-article">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【出願の表示】'" />
            </xsl:element>

            <xsl:apply-templates
                select="jp:application-reference[@appl-type = 'international-application']//jp:doc-number" />
            <xsl:apply-templates
                select="jp:application-reference[@appl-type = 'international-application']//jp:date" />
            <xsl:for-each
                select="jp:application-reference[@appl-type = 'international-application']">
                <xsl:call-template name="出願書類参照編集" />
            </xsl:for-each>
            <xsl:apply-templates select="jp:appeal-reference/jp:doc-number" />
            <xsl:apply-templates select="jp:appeal-reference/jp:date" />
            <xsl:apply-templates
                select="jp:application-reference[@appl-type = 'application']//jp:doc-number" />
            <xsl:apply-templates
                select="jp:application-reference[@appl-type = 'registration']//jp:doc-number" />
            <xsl:apply-templates
                select="jp:application-reference[@appl-type = 'examined-pub']//jp:doc-number" />
            <xsl:apply-templates
                select="jp:application-reference[@appl-type = 'un-examined-pub']//jp:doc-number" />
            <xsl:apply-templates
                select="jp:application-reference[@appl-type = 'application']//jp:date" />
            <xsl:apply-templates select="jp:file-reference-id" />
            <xsl:apply-templates select="jp:receipt-number" />
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:notice-contents-group 届出の内容
         ====================================================================-->
    <xsl:template match="jp:notice-contents-group">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:choose>
                    <xsl:when test="$node = 'jp:application-a631'">
                        <xsl:value-of select="'【確認事項】'" />
                    </xsl:when>
                    <xsl:when
                        test="$node = 'jp:application-a632' or $node = 'jp:application-a635'">
                        <xsl:value-of select="'【職権作成の表示】'" />
                    </xsl:when>
                    <xsl:otherwise>
                        <xsl:value-of select="'【届出の内容】'" />
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         氏名又は名称原語表記編集 の書換
         original <xsl:template name="氏名又は名称原語表記編集">
         jp:applicant or jp:agent
           /jp:addressbook/jp:original-language-of-name?
         ====================================================================-->
    <xsl:template match="jp:addressbook/jp:original-language-of-name">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【氏名又は名称原語表記】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         事件との関係編集
         <xsl:template name="事件との関係編集">
         ====================================================================-->
    <xsl:template match="jp:applicant//jp:relation-of-case">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【事件との関係】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- ====================================================================
         jp:representative-applicant 代表出願人 
         jp:office-address 就業場所 
         jp:attorney 弁理士 
         jp:lawyer 弁護士
         ====================================================================-->
    <xsl:template
        match="jp:representative-applicant | jp:office-address |
         jp:attorney | jp:lawyer">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="key('tags-table-key-1', local-name(), $tags-table-1)/@value" />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <xsl:key name="tags-table-key-1" match="item" use="@tag" />
    <xsl:variable name="tags-table-1">
        <item tag="representative-applicant" value="【代表出願人】" />
        <item tag="office-address" value="【就業場所】" />
        <item tag="attorney" value="【弁理士】" />
        <item tag="lawyer" value="【弁護士】" />
    </xsl:variable>

    <!-- ====================================================================
         jp:dispatch-number 発送番号編集
         jp:general-power-of-attorney-id 包括委任状番号
         jp:receipt-number 受付番号編集
         jp:citation 援用の表示
         jp:law-of-industrial-regenerate 産業再生法
         jp:relation-attorney-special-matter 代理関係の特記事項
         jp:contact 連絡先
         jp:fax ファクシミリ番号
         jp:phone 電話番号
         jp:legal-entity-property 法人の法的性質
         jp:office 営業所
         jp:office-in-japan 日本における営業所
         jp:trust-relation 信託関係事項
         jp:name 氏名又は名称 (jp:name のdefault(otherwise)部分) 
         jp:kana フリガナ
         jp:text 住所又は居所
         jp:registered-number 識別番号
         jp:addressed-to-person あて先
         jp:file-reference-id 整理番号
         jp:dtext その他 (のデフォルト(otherwise)を抽出)
         ==================================================================== -->
    <xsl:template
        match="jp:dispatch-number | jp:general-power-of-attorney-id |
         jp:receipt-number | jp:citation | jp:law-of-industrial-regenerate |
         jp:relation-attorney-special-matter | jp:contact | jp:fax | jp:phone |
         jp:legal-entity-property | jp:office | jp:office-in-japan | jp:trust-relation |
         jp:name | jp:kana | jp:text | jp:registered-number | 
         jp:addressed-to-person | jp:file-reference-id | jp:dtext">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="local-name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="key('tags-table-key-2', local-name(), $tags-table-2)/@value" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <xsl:key name="tags-table-key-2" match="item" use="@tag" />
    <xsl:variable name="tags-table-2">
        <item tag="dispatch-number" value="【発送番号】" />
        <item tag="general-power-of-attorney-id" value="【包括委任状番号】" />
        <item tag="receipt-number" value="【受付番号】" />
        <item tag="citation" value="【援用の表示】" />
        <item tag="law-of-industrial-regenerate" value="【国等の委託研究の成果に係る記載事項】" />
        <item tag="relation-attorney-special-matter" value="【代理関係の特記事項】" />
        <item tag="contact" value="【連絡先】" />
        <item tag="fax" value="【ファクシミリ番号】" />
        <item tag="phone" value="【電話番号】" />
        <item tag="legal-entity-property" value="【法人の法的性質】" />
        <item tag="office" value="【営業所】" />
        <item tag="office-in-japan" value="【日本における営業所】" />
        <item tag="trust-relation" value="【信託関係事項】" />
        <item tag="name" value="【氏名又は名称】" />
        <item tag="kana" value="【フリガナ】" />
        <item tag="text" value="【住所又は居所】" />
        <item tag="registered-number" value="【識別番号】" />
        <item tag="addressed-to-person" value="【あて先】" />
        <item tag="file-reference-id" value="【整理番号】" />
        <item tag="dtext" value="【その他】" />
    </xsl:variable>

    <!-- override build-in template for text and attribute nodes. -->
    <xsl:template match="text()|@*">
        <!-- <xsl:value-of select="normalize-space(.)"/> -->
    </xsl:template>


</xsl:stylesheet>