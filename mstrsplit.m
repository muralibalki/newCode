function vec=mstrsplit(str,delim)

prevEnd=1;
count=1;
i=1;
flag=1;
while i<=length(str)
        if str(i)=='"'
                flag=~flag;
        end
        if ((str(i)==delim) || i==length(str)) & flag
                vec{count}=str(prevEnd:i-1);
                if vec{count}(1)=='"'
                    vec{count}=vec{count}(2:end);
                end
                if vec{count}(end)=='"'
                    vec{count}=vec{count}(1:(end-1));
                end
                count=count+1;
                prevEnd=i+1;
        end
        i=i+1;
end
