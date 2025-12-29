<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp">

    <!-- 文字列処理関連のテンプレート -->

    <!-- 
         split $input-string at every $n-chars and insert $sep to splitted positions.
    -->
    <xsl:template name="split-at-n-chars">
        <xsl:param name="input-string" as="xs:string" />
        <xsl:param name="n-chars" as="xs:integer" />
        <xsl:param name="sep" as="xs:string" select="' '" />
        <xsl:variable name="length" select="string-length($input-string)" />

        <xsl:for-each select="for $i in 1 to $length div $n-chars return $i">
            <xsl:value-of
                select="substring($input-string, (position() - 1) * $n-chars + 1, $n-chars)" />
            <xsl:if test="position() != last()">
                <xsl:value-of select="$sep" />
            </xsl:if>
        </xsl:for-each>
    </xsl:template>

</xsl:stylesheet>