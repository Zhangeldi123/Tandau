from rest_framework import serializers
from quiz import models as model_file

class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type':'password'})
    class Meta:
        model = model_file.Users
        fields = ['email','name','password','password2']
        extra_kwargs ={
            'password':{'write_only':True}
        }
    def validate(self,attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError("Both password should be matched")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        return model_file.Users.objects.create_user(**validated_data)

class UserLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=100)
    class Meta:
        model = model_file.Users
        fields = ['email','password']