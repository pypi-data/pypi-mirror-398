<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp">

    <xsl:variable name="law">
        <xsl:choose>
            <xsl:when
                test="//procedure-param[@name='law' and text() = '1']">patent</xsl:when>
            <xsl:when
                test="//procedure-param[@name='law' and text() = '2']">utility-model</xsl:when>
            <xsl:otherwise>unknown</xsl:otherwise>
        </xsl:choose>
    </xsl:variable>

    <xsl:template match="/">
        <xsl:element name="root">
            <xsl:apply-templates select="root/application-body/description" />
            <xsl:apply-templates select="root/application-body/claims" />
            <xsl:apply-templates select="root/application-body/abstract" />
            <xsl:apply-templates select="root/application-body/drawings" />
        </xsl:element>
    </xsl:template>

    <!-- 明細書 -->
    <xsl:template
        match="description">
        <xsl:element name="blocks">
            <xsl:element name="tag">description</xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="key('tags-table-key', 'description', $tags-table)/@jp-tag" />
            </xsl:element>
            <xsl:apply-templates />

            <xsl:element name="indent-level">0</xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 発明/考案の名称 -->
    <xsl:template
        match="invention-title">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of
                    select="key('tags-table-key', name() || '-' || $law, $tags-table)/@jp-tag" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
            <xsl:element name="indent-level">0</xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 特実で切り分けが不要な要素  -->
    <!-- 技術分野, 背景技術, 先行技術文献，特許文献，非特許文献，
         解決手段、図面の簡単な説明
         産業上の利用可能性,符号の説明, 配列表,符号の説明,受託番号 -->
    <xsl:template
        match="technical-field | background-art |
        citation-list | patent-literature | non-patent-literature |
        tech-solution | description-of-drawings |
        industrial-applicability | sequence-list-text | reference-signs-list |
        reference-to-deposited-biological-material">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="key('tags-table-key', name(), $tags-table)/@jp-tag" />
            </xsl:element>
            <xsl:if test="*[1]">
                <xsl:apply-templates />
            </xsl:if>
            <xsl:element name="indent-level">0</xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 特実で切り分けが必要な要素  -->
    <!-- 解決しようとする課題,  効果, 実施形態 -->
    <xsl:template
        match="summary-of-invention | disclosure |
        tech-problem | advantageous-effects |
        description-of-embodiments | best-mode">
        <xsl:element name="blocks">
            <xsl:element name="tag">
                <xsl:value-of select="name()" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of
                    select="key('tags-table-key', name() || '-' || $law, $tags-table)/@jp-tag" />
            </xsl:element>
            <xsl:if test="*[1]">
                <xsl:apply-templates />
            </xsl:if>
            <xsl:element name="indent-level">0</xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 特許文献 -->
    <xsl:template
        match="patcit">
        <xsl:element name="blocks">
            <xsl:element name="tag">patcit</xsl:element>
            <xsl:element name="number">
                <xsl:value-of select="@num" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【特許文献' || @num || '】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="./text" />
            </xsl:element>
            <xsl:element name="indent-level">2</xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 非特許文献 -->
    <xsl:template
        match="nplcit">
        <xsl:element name="blocks">
            <xsl:element name="tag">nplcit</xsl:element>
            <xsl:element name="number">
                <xsl:value-of select="@num" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【非特許文献' || @num || '】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="./text" />
            </xsl:element>
            <xsl:element name="indent-level">2</xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 図面の簡単な説明 の図 -->
    <xsl:template
        match="figref">
        <xsl:element name="blocks">
            <xsl:element name="tag">figref</xsl:element>
            <xsl:element name="number">
                <xsl:value-of select="@num" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【図' || @num || '】'" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
            <xsl:element name="indent-level">2</xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 実施例 -->
    <xsl:template match="embodiments-example">
        <xsl:element name="blocks">
            <xsl:element name="tag">embodiment-example</xsl:element>
            <xsl:element name="number">
                <xsl:value-of select="@ex-num" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【実施例' || @num || '】'" />
            </xsl:element>
            <xsl:apply-templates select="p" />
            <xsl:element name="indent-level">1</xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 実施例 -->
    <xsl:template match="mode-for-invention">
        <xsl:element name="blocks">
            <xsl:element name="tag">mode-for-invention</xsl:element>
            <xsl:element name="number">
                <xsl:value-of select="@mode-num" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【実施例' || @mode-num || '】'" />
            </xsl:element>
            <xsl:apply-templates select="p" />
            <xsl:element name="indent-level">1</xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 特許請求の範囲/実用新案登録請求の範囲 -->
    <xsl:template match="claims">
        <xsl:element name="blocks">
            <xsl:element name="tag">claims</xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of
                    select="key('tags-table-key', 'claims-' || $law, $tags-table)/@jp-tag" />
            </xsl:element>
            <xsl:element name="indent-level">0</xsl:element>
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>

    <!-- 請求項 -->
    <xsl:template match="claim">
        <xsl:element name="blocks">
            <xsl:element name="tag">claim</xsl:element>
            <xsl:element name="jp-tag">【請求項<xsl:value-of select="@num" />】</xsl:element>
            <xsl:element name="number">
                <xsl:value-of select="@num" />
            </xsl:element>
            <xsl:element name="indent-level">0</xsl:element>
            <xsl:element name="isIndependent">
                <xsl:choose>
                    <xsl:when test="claim-text[contains(., '請求項')]">false</xsl:when>
                    <xsl:otherwise>true</xsl:otherwise>
                </xsl:choose>
            </xsl:element>
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>

    <!-- 請求項の文言 -->
    <xsl:template match="claim-text">
        <xsl:element name="blocks">
            <xsl:element name="tag">claim-text</xsl:element>
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>

    <!-- 図面 -->
    <xsl:template match="drawings">
        <xsl:element name="blocks">
            <xsl:element name="tag">drawings</xsl:element>
            <xsl:element name="indent-level">0</xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="key('tags-table-key', 'drawings', $tags-table)/@jp-tag" />
            </xsl:element>
            <xsl:apply-templates select="figure" />
        </xsl:element>
    </xsl:template>

    <!-- 要約書 -->
    <xsl:template match="abstract">
        <xsl:element name="blocks">
            <xsl:element name="tag">abstract</xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="key('tags-table-key', 'abstract', $tags-table)/@jp-tag" />
            </xsl:element>
            <xsl:element name="text">
                <xsl:call-template name="trim">
                    <xsl:with-param name="text" select="." />
                </xsl:call-template>
            </xsl:element>
            <xsl:element name="indent-level">0</xsl:element>
        </xsl:element>
    </xsl:template>

    <!--  図   -->
    <xsl:template match="figure">
        <!-- figref[@num=@num] だと集合値の比較なので失敗する 
         変数にすると単一値の比較になるので意図通りになる
         figref[@num=current()/@num] でも可
          -->
        <xsl:variable name="num" select="@num" />

        <!-- 子要素img のファイル名 -->
        <xsl:variable name="image-file" select="img/@file" />

        <xsl:element name="{name()}-list">
            <xsl:element name="tag">
                <xsl:value-of select="name()" />
            </xsl:element>
            <xsl:element name="number">
                <xsl:value-of select="@num" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:text>【</xsl:text>
                <xsl:value-of
                    select="key('tags-table-key', name(), $tags-table)/@jp-tag" />
                <xsl:value-of select="@num" />
                <xsl:text>】</xsl:text>
            </xsl:element>
            <xsl:element name="alt">
                <xsl:value-of select="name() || ' No. ' || @num || ' '" />
                <xsl:value-of
                    select="//description-of-drawings//figref[@num=$num]" />
            </xsl:element>

            <xsl:element name="representative">
                <xsl:choose>
                    <xsl:when test="//procedure-param[@file-name = $image-file]">true</xsl:when>
                    <xsl:otherwise>false</xsl:otherwise>
                </xsl:choose>
            </xsl:element>

            <xsl:element name="indent-level">0</xsl:element>

            <xsl:apply-templates select="img" />
        </xsl:element>
    </xsl:template>

    <!--  化,表,数   -->
    <xsl:template match="chemistry | tables | maths">
        <xsl:element name="{name()}-list">
            <xsl:element name="tag">
                <xsl:value-of select="name()" />
            </xsl:element>
            <xsl:element name="number">
                <xsl:value-of select="@num" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:text>【</xsl:text>
                <xsl:value-of
                    select="key('tags-table-key', name(), $tags-table)/@jp-tag" />
                <xsl:value-of select="@num" />
                <xsl:text>】</xsl:text>
            </xsl:element>

            <xsl:element name="indent-level">2</xsl:element>

            <xsl:apply-templates select="img" />
        </xsl:element>
    </xsl:template>


    <!-- 変換元XMLにある images/image のlookup -->
    <xsl:key name="images-table-key" match="/root/images/image" use="@orig" />

    <!--  イメージ   -->
    <xsl:template match="img">
        <xsl:for-each select="key('images-table-key', @file)">
            <xsl:element name="images">
                <xsl:element name="src">
                    <xsl:value-of select="@new" />
                </xsl:element>
                <xsl:element name="width">
                    <xsl:value-of select="@width" />
                </xsl:element>
                <xsl:element name="height">
                    <xsl:value-of select="@height" />
                </xsl:element>
                <xsl:element name="kind">
                    <xsl:value-of select="@kind" />
                </xsl:element>
                <xsl:element name="size_tag">
                    <xsl:value-of select="@size_tag" />
                </xsl:element>
            </xsl:element>
        </xsl:for-each>
    </xsl:template>

    <!-- 段落 -->
    <xsl:template
        match="p">
        <xsl:element name="blocks">
            <xsl:element name="tag">paragraph</xsl:element>
            <xsl:element name="indent-level">1</xsl:element>
            <xsl:element name="number">
                <xsl:value-of select="@num" />
            </xsl:element>
            <xsl:element name="jp-tag">
                <xsl:value-of select="'【' || @num || '】'" />
            </xsl:element>
            <xsl:apply-templates />
        </xsl:element>
    </xsl:template>

    <!-- 上付 -->
    <xsl:template
        match="sup">
        <xsl:element name="blocks">
            <xsl:element name="tag">super</xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 下付 -->
    <xsl:template
        match="sub">
        <xsl:element name="blocks">
            <xsl:element name="tag">sub</xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- 下線 -->
    <xsl:template
        match="u">
        <xsl:element name="blocks">
            <xsl:element name="tag">underline</xsl:element>
            <xsl:element name="text">
                <xsl:value-of select="." />
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- テキストノード -->
    <xsl:template
        match="text()">
        <xsl:if test="normalize-space(.) != ''">
            <xsl:element name="blocks">
                <xsl:element name="tag">text</xsl:element>
                <xsl:element name="text">
                    <xsl:call-template name="trim">
                        <xsl:with-param name="text" select="." />
                    </xsl:call-template>
                </xsl:element>
            </xsl:element>
        </xsl:if>
    </xsl:template>

    <xsl:key name="tags-table-key" match="item" use="@tag" />
    <xsl:variable name="tags-table">
        <item tag="description" jp-tag="【書類名】 明細書" />
        <item tag="claims-patent" jp-tag="【書類名】 特許請求の範囲" />
        <item tag="claims-utility-model" jp-tag="【書類名】 実用新案登録請求の明細書" />
        <item tag="drawings" jp-tag="【書類名】 図面" />
        <item tag="abstract" jp-tag="【書類名】 要約書" />
        <item tag="invention-title-patent" jp-tag="【発明の名称】" />
        <item tag="invention-title-utility-model" jp-tag="【考案の名称】" />
        <item tag="technical-field" jp-tag="【技術分野】" />
        <item tag="background-art" jp-tag="【背景技術】" />
        <item tag="citation-list" jp-tag="【先行技術文献】" />
        <item tag="patent-literature" jp-tag="【特許文献】" />
        <item tag="non-patent-literature" jp-tag="【非特許文献】" />
        <item tag="disclosure-patent" jp-tag="【発明の開示】" />
        <item tag="disclosure-utility-model" jp-tag="【考案の開示】" />
        <item tag="summary-of-invention-patent" jp-tag="【発明の概要】" />
        <item tag="summary-of-invention-utility-model" jp-tag="【考案の概要】" />
        <item tag="tech-problem-patent" jp-tag="【発明が解決しようとする課題】" />
        <item tag="tech-problem-utility-model" jp-tag="【考案が解決しようとする課題】" />
        <item tag="tech-solution" jp-tag="【課題を解決する手段】" />
        <item tag="advantageous-effects-patent" jp-tag="【発明の効果】" />
        <item tag="advantageous-effects-utility-model" jp-tag="【考案の効果】" />
        <item tag="description-of-drawings" jp-tag="【図面の簡単な説明】" />
        <item tag="description-of-embodiments-patent" jp-tag="【発明を実施するための形態】" />
        <item tag="description-of-embodiments-utility-model" jp-tag="【考案を実施するための形態】" />
        <item tag="best-mode-patent" jp-tag="【発明を実施するための最良の形態】" />
        <item tag="best-mode-utility-model" jp-tag="【考案を実施するための最良の形態】" />
        <item tag="sequence-list-text" jp-tag="【配列表】" />
        <item tag="industrial-applicability" jp-tag="【産業上の利用可能性】" />
        <item tag="reference-signs-list" jp-tag="【符号の説明】" />
        <item tag="sequence-list-text" jp-tag="【配列表フリーテキスト】" />
        <item tag="mode-for-invention" jp-tag="【実施例】" />
        <item tag="reference-to-deposited-biological-material" jp-tag="【受託番号】" />
        <item tag="figure" jp-tag="図" />
        <item tag="chemistry" jp-tag="化" />
        <item tag="tables" jp-tag="表" />
        <item tag="maths" jp-tag="数" />
    </xsl:variable>

    <!-- 先頭と最後の空白/改行の除去 -->
    <xsl:template
        name="trim">
        <xsl:param name="text" />
        <xsl:value-of select="replace($text, '^[\s]+|[\s]+$', '')" />
    </xsl:template>

</xsl:stylesheet>